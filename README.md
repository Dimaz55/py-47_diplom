**Для запуска проекта наберите:**

`docker-compose up --build`
___
**Регистрация пользователя:**

```http request
POST /users/register/
```
```
{
  "last_name": str, // Фамилия
  "first_name": str, // Имя
  "patronymic": str, // Отчество
  "company": str, // Название компании
  "role": str, // "seller" продавец | "buyer" покупатель
  "email": str, // Адрес эл.почты
  "password": str // Пароль
}
```
___
**Получение токена (логин):**
```
Запрос:
{
  "email": "email@example.com",
  "password": "YourSuperPassword"
}

Ответ:
{
  "token": "your_token"
}
```
___
**Выгрузка прайс-листа (только для продавцов {"role": "seller"}):**
```http request
POST /upload/
Authorization: Token <your_token>
Content-Type: multipart/form-data;
```
```html
<form>
  <input type="file" name="file">
</form>

```
Формат прайс-листа - **CSV**.
Названий характеристик и их значений может быть несколько.

Структура файла:
```
Категория,Бренд,Модель,Артикул,Количество,Цена товара,Цена доставки,(Название характеристики,
Значение характеристики)...
```
___
**Просмотр товаров**

Список товаров:
```http request
GET /products/
```
Ответ:
```
{
  "id": int,
  "sku": str, // Уникальный артикул модификации товара
  "brand": str, // Название бренда
  "title": str, // Название модели
  "category": str, // Категория товара
  "prices": [       // Список цен поставщиков
    {
      "id": int, // Идентификатор цены товара для заказа
      "product_price": int, // Стоимость товара
      "delivery_price": int, // Стоимость доставки
      "quantity": int, // Количество доступное для заказа
      "orderable": bool, // Принимает-ли продавец заказы
      "seller": str, // Наименование продавца
      "price_date": datetime // Дата и время обновления цены
    },
   ...
  ]
}
```
Карточка товара:
```http request
GET /products/<product_id>/
```
Ответ аналогичен списку, но добавлены характеристики товара:
```
{
  "props": [
    {
      "title": str, // Название характеристики
      "value": str // Значение характеристики
    },
    ...
  ]
}
```
___
**Заказ товаров (доступно только покупателям {"role": "buyer"}):**
```http request
POST /cart/
Authorization: Token <your_token>
```

Запрос:
```
[
  {
    "pricelist": int, // Идентификатор цены товара для заказа
    "quantity": int // Количество
  },
  ...
]
```
Ответ:
```
{
  "id": int, // Номер заказа
  "status": str, // Статус заказа
  "address": str, // Адрес доставки
  "items": [ // Список заказанных товаров
    {
      "title": str, // Название товара
      "product_price": int, // Цена за единицу
      "delivery_price": int, // Стоимость доставки
      "quantity": int, // Количество заказнных единиц
      "seller": str, // Наименование продавца
    },
    ...
  ],
  "summary": {
    "products_total": int, // Стоимость товаров
    "delivery_total": int, // Стоимость доставки
    "total": int // Итоговая сумма
  }
}
```
___
**Просмотр заказов:**
Список:
```http request
GET /orders/
Authorization: Token <your_token>
```
Карточка заказа:
```http request
GET /orders/<id>/
Authorization: Token <your_token>
```
Ответ зависит от роли пользователя: продавцы видят только заказы с их товарами, покупатель видит 
только свои заказы. Выдача аналогична ответу в создании заказа.