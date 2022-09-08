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
**Заказ товаров (Ещё не реализовано):**
```http request
POST /orders/
Authorization: Token <your_token>
```

Запрос:
```
[
  {
    "id": int, // Идентификатор цены товара для заказа
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
  "products": [
    {
      "sku": str, // Артикул товара
      "quantity": int, // Количество заказанных единиц
      "total_price": int, // Общая стоимость
      "delivery_price": int // Стоимость доставки
    },
    ...
  ]
}
```
