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
from module2 import MainWindow, BaseWindow
class AuthWindow(BaseWindow):

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

    def auth(self):
        login = self.loginInput.text()
        password = self.passwordInput.text()
        with Session() as session:
            user = session.query(User).filter_by(
                login=login,
                password=password
            ).first()
            if not user:
                return QMessageBox.critical(
                    self,
                    "Ошибка",
                    "Логин или пароль неверный!"
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
        self.descriptionLabel = QLabel(
            f"Описание: {product.description}"
        )
        self.manufacturerLabel = QLabel(
            f"Производитель: {product.manufacturer.name}"
        )
        self.supplierLabel = QLabel(
            f"Поставщик: {product.supplier.name}"
        )
        if not product.discount:
            self.priceLabel = QLabel(
                f"Цена: {product.price} руб."
            )
        else:
            self.priceLabel = QLabel(
                f"Цена: <s style='color: red'>{product.price}</s> "
                f"<span style='color: black'>{product.price_count}</span> руб."
            )
        self.measureLabel = QLabel(
            f"Единица измерения: {product.measure_type}"
        )
        self.quantityLabel = QLabel(
            f"Количество на складе: {product.quantity}"
        )
        if not product.quantity:
            self.quantityLabel.setStyleSheet(
                'background-color: #4444AA;'
            )
        for label in [
            self.nameLabel,
            self.descriptionLabel,
            self.manufacturerLabel,
            self.supplierLabel,
            self.priceLabel,
            self.measureLabel,
            self.quantityLabel
        ]:
            self.layout.addWidget(label)
        self.mainLayout.addLayout(self.layout)
        self.mainLayout.addStretch()
        if product.discount:
            self.discountLabel = QLabel(
                f"Действующая скидка: {product.discount}%"
            )
            self.mainLayout.addWidget(self.discountLabel)
            self.mainLayout.addStretch()
        self.setLayout(self.mainLayout)
        self.setObjectName("ProductCard")
        if product.discount > 15:
            self.setStyleSheet(
                "#ProductCard {background:#2E8B57}"
            )

class ProductsWindow(BaseWindow):
    def refresh(self):
        productContent = QWidget()
        scrollLayout = QVBoxLayout(productContent)
        with Session() as session:
            products = session.query(Product).join(
                Company,
                Product.manufacturer_id == Company.id
            ).options(
                joinedload(Product.manufacturer),
                joinedload(Product.supplier)
            ).all()
        for product in products:
            scrollLayout.addWidget(QProductWidget(product))
        self.scroll.setWidget(productContent)

    def __init__(self):
        super().__init__("Список товаров")
        self.view = QVBoxLayout()
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.logoutBtn = QPushButton("Выйти")
        self.logoutBtn.clicked.connect(self.logout)
        self.view.addWidget(self.scroll)
        self.header.addWidget(self.logoutBtn)
        self.layout.addLayout(self.view)

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
    sys.exit(app.exec())
    # 94d5ous@gmail.com
    # uzWC67
