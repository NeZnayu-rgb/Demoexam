import sys

from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap, Qt
from PySide6.QtWidgets import (
    QApplication,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLabel,
    QScrollArea,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QFrame
)
from sqlalchemy.orm import joinedload

from module1 import User, Session, Product, Company
from module2 import MainWindow
from module3 import (
    FilterProductWidget,
    BackwardMixin,
    ProductForm,
    delete_product
)
from module4 import OrderWindow

class AuthWindow(BackwardMixin):
    def __init__(self):
        super().__init__("Войти")
        layout = QVBoxLayout(form := QWidget())

        self.loginInput = QLineEdit()
        self.loginInput.setPlaceholderText("Ввести логин")
        self.passwordInput = QLineEdit()
        self.passwordInput.setPlaceholderText("Ввести пароль")

        self.authBtn = QPushButton("Войти")
        self.guestBtn = QPushButton("Зайти как гость")
        self.authBtn.clicked.connect(self.auth)
        self.guestBtn.clicked.connect(self.close)

        layout.addWidget(self.loginInput)
        layout.addWidget(self.passwordInput)
        layout.addWidget(self.authBtn)
        layout.addWidget(self.guestBtn)

        self.layout.addWidget(form, alignment=Qt.AlignmentFlag.AlignHCenter)

    def close(self, user: User = None):
        MainWindow.set_user(user)

        MainWindow.set_window(
            ProductsWindow()
        ).show()
        self.hide()

    def autologin(self):
        self.loginInput.setText("94d5ous@gmail.com")
        self.passwordInput.setText("uzWC67")
        self.auth()

    def auth(self):
        login = self.loginInput.text()
        password = self.passwordInput.text()

        with Session() as session:
            user = session.query(User).filter_by(login=login, password=password).first()
            if not user:
                return QMessageBox.critical(
                    self,
                    "Ошибка",
                    "Логин иои пароль не верный!"
                )
            self.close(user)

class QProductWidget(QFrame):
    def __init__(self, product: Product):
        super().__init__()
        self.mainLayout = QHBoxLayout()

        image = QPixmap(product.valid_photo)
        self.imageLabel = QLabel()
        self.imageLabel.setPixmap(image.scaled(QSize(100, 100)))
        self.imageLabel.setStyleSheet("width: 100px;")
        self.mainLayout.addWidget(self.imageLabel)
        self.mainLayout.addStretch()

        self.layout = QVBoxLayout()
        self.nameLabel = QLabel(f"{product.category} | {product.name}")
        self.nameLabel.setStyleSheet('font-weight: bold;')
        self.descriptionLabel = QLabel(f"Описание: {product.description}")
        self.manufacturerLabel = QLabel(f"Производитель: {product.manufacturer.name}")
        self.supplierLabel = QLabel(f"Поставщик: {product.supplier.name}")
        if not product.discount:
            self.priceLabel = QLabel(f"Цена: {product.price} руб.")
        else:
            self.priceLabel = QLabel(
                f"Цена: <s style='color: red'>{product.price}</s> "
                f"<span style='color: black'>{product.fixed_price}</span> руб."
            )
        self.measureLabel = QLabel(f"Единица измерения: {product.measure_type}")
        self.quantityLabel = QLabel(f"Количество на складе: {product.quantity}")
        if not product.quantity:
            self.quantityLabel.setStyleSheet('background-color: #4444AA;')

        for label in [
            self.nameLabel, self.descriptionLabel, self.manufacturerLabel,
            self.supplierLabel, self.priceLabel, self.measureLabel, self.quantityLabel
        ]:
            self.layout.addWidget(label)
        self.mainLayout.addLayout(self.layout)

        self.mainLayout.addStretch()

        if product.discount:
            self.discountLabel = QLabel(f"Действующая скидка: {product.discount}%")
            self.mainLayout.addWidget(self.discountLabel)
            self.mainLayout.addStretch()

        if (user := MainWindow.get_user()) and user.role == "Администратор":
            self.actionLayout = QVBoxLayout()

            self.deleteBtn = QPushButton("Удалить")
            self.deleteBtn.clicked.connect(self.delete(product))
            self.actionLayout.addWidget(self.deleteBtn)

            self.editBtn = QPushButton("Редактировать")
            self.editBtn.clicked.connect(self.open_edit_form(product))
            self.actionLayout.addWidget(self.editBtn)

            self.mainLayout.addLayout(self.actionLayout)

        self.setLayout(self.mainLayout)
        self.setObjectName("ProductCard")
        if product.discount > 15:
            self.setStyleSheet("""#ProductCard {background:#2E8B57}""")

    def delete(self, product: Product):
        def inner():
            if delete_product(product):
                self.setParent(None)
                self.deleteLater()
        return inner

    @staticmethod
    def open_edit_form(product: Product):
        def inner():
            prevWindow = MainWindow()
            MainWindow.set_window(
                ProductForm("Редактирование товара", product=product)
            ).show()
            prevWindow.hide()
        return inner


# BackwardMixin это уже 3-ий модуль. Для второго достаточно отнаследовать от BaseWindow
class ProductsWindow(BackwardMixin):

    def refresh(self, filters: tuple = (), order_by: tuple = ()):
        productContent = QWidget()
        scrollLayout = QVBoxLayout(productContent)

        with Session() as session:
            products = session.query(Product).where(
                *filters
            ).join(
                Company, Product.manufacturer_id == Company.id
            ).options(
                joinedload(Product.manufacturer),
                joinedload(Product.supplier)
            ).order_by(*order_by).all()

        for product in products:
            scrollLayout.addWidget(QProductWidget(product))
        self.scroll.setWidget(productContent)

    def __init__(self):
        super().__init__("Список товаров")

        self.view = QVBoxLayout()
        user = MainWindow.get_user()

        if user and user.role in ["Менеджер", "Администратор"]:
            self.view.addWidget(FilterProductWidget(self.refresh))
            self.header.addWidget(btn := QPushButton("Заказы"))
            btn.clicked.connect(self.open_order_page)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.logoutBtn = QPushButton("Выйти")
        self.logoutBtn.clicked.connect(self.logout)

        self.view.addWidget(self.scroll)
        if user and user.role == "Администратор":
            self.createBtn = QPushButton("Создать новый товар")
            self.createBtn.clicked.connect(self.open_create_form)
            self.view.addWidget(self.createBtn)

        self.header.addWidget(self.logoutBtn)
        self.layout.addLayout(self.view)

    def open_order_page(self):
        MainWindow.set_window(
            OrderWindow("Список заказов")
        ).show()
        self.hide()

    def open_create_form(self):
        MainWindow.set_window(
            ProductForm("Создание товара", product=None)
        ).show()
        self.hide()

    def show(self):
        self.refresh()
        super().show()

    def logout(self):
        MainWindow.set_window(None)
        MainWindow.set_user(None)
        MainWindow.set_window(
            AuthWindow()
        ).show()
        self.hide()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    MainWindow.set_window(
        a := AuthWindow()
    ).show()
    a.autologin()
    sys.exit(app.exec())
