import os
from datetime import datetime
from pathlib import Path
from typing import List, Any

from sqlalchemy import (
    Column, Integer, create_engine,
    String, Float, ForeignKey,
    UniqueConstraint, DateTime
)
from sqlalchemy.orm import (
    DeclarativeBase,
    relationship,
    sessionmaker)

import openpyxl



engine = create_engine("postgresql+psycopg2://{}:{}@{}:{}/{}".format(
    "postgres", "Temmie2504", "localhost", "5432", "new_test"
))
Session = sessionmaker(bind=engine)
ROOT = Path(__file__).parent.resolve()

def get_data(filepath: str, first_line_pass: bool = True) -> List[List[Any]]:
    sheet = openpyxl.load_workbook(filepath).active
    return [
        [val.value for val in row]
        for row in list(sheet.iter_rows())[int(first_line_pass):]
        if row[0].value
    ]

class Base(DeclarativeBase):
    __abstract__ = True


class Company(Base):
    __tablename__ = "company"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)


class Product(Base):
    __tablename__ = "product"
    articul = Column(String, primary_key=True)
    name = Column(String)
    measure_type = Column(String)
    price = Column(Float)

    supplier_id = Column(Integer, ForeignKey("company.id"))
    supplier = relationship(Company, foreign_keys=[supplier_id])

    manufacturer_id = Column(Integer, ForeignKey("company.id"))
    manufacturer = relationship(Company, foreign_keys=[manufacturer_id])
    category = Column(String)
    discount = Column(Float, default=0)
    quantity = Column(Integer)
    description = Column(String)
    photo = Column(String, nullable=True)

    @property
    def fixed_price(self):
        return round(self.price * (1 - self.discount / 100), 2)

    @property
    def valid_photo(self):
        if self.photo and os.path.exists(self.photo):
            return self.photo
        return str(ROOT / 'import/picture.png')


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    role = Column(String)
    fio = Column(String)
    login = Column(String, unique=True)
    password = Column(String)


class Address(Base):
    __tablename__ = "address"
    id = Column(Integer, primary_key=True)
    description = Column(String)


class OrderItem(Base):
    __tablename__ = "order_item"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("order.id"))
    articul = Column(String, ForeignKey("product.articul"))
    quantity = Column(Integer)
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product")

    __table_args__ = (UniqueConstraint("order_id", "articul"),)


class Order(Base):
    __tablename__ = "order"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, nullable=True)
    deliver_at = Column(DateTime, nullable=True)
    address_id = Column(Integer, ForeignKey("address.id"))
    user_id = Column(Integer, ForeignKey("user.id"))
    address = relationship("Address")
    user = relationship("User")
    code = Column(Integer)
    status = Column(String)

    order_items = relationship(OrderItem, back_populates="order", cascade="all, delete")

    @property
    def articuls(self):
        return ", ".join(oi.product.articul for oi in self.order_items)

def main():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    data = get_data("import/Tovar.xlsx")

    companies_names = list(set([row[4] for row in data]) | set([row[5] for row in data]))

    with Session() as session:
        companies_list = [Company(name=name) for name in companies_names]
        session.bulk_save_objects(companies_list, return_defaults=True)
        session.commit()

    companies = {c.name: c.id for c in companies_list}

    with Session() as session:
        products = [
            Product(
                articul=row[0],
                name=row[1],
                measure_type=row[2],
                price=row[3],
                supplier_id=companies[row[4]],
                manufacturer_id=companies[row[5]],
                category=row[6],
                discount=row[7],
                quantity=row[8],
                description=row[9],
                photo=(row[10] and str(ROOT / 'import' / row[10])) or None
            )
            for row in data
        ]
        session.bulk_save_objects(products)
        session.commit()

    data = get_data("import/user_import.xlsx")
    with Session() as session:
        users = [
            User(
                role=row[0],
                fio=row[1],
                login=row[2],
                password=row[3]
            )
            for row in data
        ]
        session.bulk_save_objects(users, return_defaults=True)
        session.commit()
    users = {val.fio: val.id for val in users}

    data = get_data("import/Пункты выдачи_import.xlsx", first_line_pass=False)
    with Session() as session:
        addresses = [Address(description=row[0]) for row in data]
        session.bulk_save_objects(addresses, return_defaults=True)
        session.commit()

    data = get_data("import/Заказ_import.xlsx")

    order_items = [
        OrderItem(
            order_id=row[0],
            articul=row_data[0],
            quantity=row_data[1]
        )
        for row in data
        for row_data in zip(row[1].split(", ")[::2], row[1].split(", ")[1::2])
    ]

    with Session() as session:
        orders = [
            Order(
                created_at=row[2] if isinstance(row[2], datetime) else datetime(year=2025, month=3, day=2),
                deliver_at=row[3],
                address_id=row[4],
                user_id=users[row[5]],
                code=row[6],
                status=row[7].strip()
            )
            for row in data
        ]
        session.bulk_save_objects(orders)
        session.bulk_save_objects(order_items)
        session.commit()

if __name__ == '__main__':
    main()




