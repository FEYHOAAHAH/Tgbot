import asyncio
import uuid

import aiogram
import aiogram.dispatcher
import aiogram.dispatcher.filters
import aiogram.types
import psycopg2
from aiogram import executor, types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Command, Text


# Создание класса состояний для регистрации пользователя
class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_address = State()
    waiting_for_email = State()


# Создание подключения к базе данных
conn = psycopg2.connect(database="dbtwo", user="postgres", password="pass001", host="localhost",
                        port="5432")

# Создание объекта курсора для выполнения операций с базой данных
cur = conn.cursor()

# Создание таблицы, если она еще не существует
cur.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        client_id SERIAL PRIMARY KEY,
        client_chat_id UUID DEFAULT uuid_generate_v4() UNIQUE,
        client_name VARCHAR(255),
        client_phone VARCHAR(255),
        client_adress VARCHAR(255)
    );
""")
conn.commit()

# Создание бота и диспетчера
bot = aiogram.Bot(token="6685532237:AAEdUgC9ETWYA1BAZaCKlKwdPI1obWs4ebU")
storage = MemoryStorage()
dp = aiogram.dispatcher.Dispatcher(bot, storage=storage)


# Обработчик команды /reg
@dp.message_handler(commands=["reg"])
async def start(message: aiogram.types.Message):
    await message.answer("Регистрация. Введите ваше имя")
    await RegistrationStates.waiting_for_name.set()


# Обработчик сообщений в состоянии ожидания имени пользователя
@dp.message_handler(state=RegistrationStates.waiting_for_name)
async def process_name(message: aiogram.types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await RegistrationStates.next()
    await message.answer("Введите свой телефон:")


# Обработчик сообщений в состоянии ожидания телефона пользователя
@dp.message_handler(state=RegistrationStates.waiting_for_phone)
async def process_phone(message: aiogram.types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await RegistrationStates.next()
    await message.answer("Введите свой адрес:")


@dp.message_handler(state=RegistrationStates.waiting_for_address)
async def process_phone(message: aiogram.types.Message, state: FSMContext):
    await state.update_data(adress=message.text)
    await RegistrationStates.next()
    await message.answer("Введите свой email:")


# Обработчик сообщений в состоянии ожидания адреса пользователя
@dp.message_handler(state=RegistrationStates.waiting_for_email)
async def process_email(message: aiogram.types.Message, state: FSMContext):
    await state.update_data(email=message.text)

    data = await state.get_data()

    # Вставка данных в базу данных
    client_chat_id = str(uuid.uuid4())

    cur.execute("""
        INSERT INTO clients (client_chat_id, client_name, client_phone, client_adress, client_email)
        VALUES (%s, %s, %s, %s, %s)
     """, (client_chat_id, data['name'], data['phone'], data['adress'], data['email']))
    conn.commit()

    # Сброс состояния
    await state.finish()

    await message.answer("Спасибо за регистрацию! Данные сохранены")


# ----------------------------------------------------------------------------------------------------------------------


cur = conn.cursor()

create_table_query = """
    CREATE TABLE IF NOT EXISTS cart (
        cart_id SERIAL PRIMARY KEY,
        user_id INT,
        product_name VARCHAR(255),
        datetime_created DATE,
        last_ordered DATE
    )
"""
cur.execute(create_table_query)
conn.commit()


class AddToCartStates(StatesGroup):
    state_product = State()


@dp.message_handler(Command("add_to_cart"))
async def start_add_to_cart(message: types.Message):
    await message.answer("Введите название продукта, который вы хотите добавить в корзину:")
    await AddToCartStates.state_product.set()


@dp.message_handler(state=AddToCartStates.state_product)
async def process_product(message: types.Message, state: FSMContext):
    product_name = message.text

    # Сохранение продукта в корзину
    cur = conn.cursor()
    insert_query = """
        INSERT INTO cart (user_id, product_name, datetime_created)
        VALUES (%s, %s, CURRENT_DATE)
    """
    cur.execute(insert_query, (message.from_user.id, product_name))
    conn.commit()

    await message.answer(f"Продукт '{product_name}' добавлен в корзину!")

    # Сброс состояния
    await state.finish()


# ----------------------------------------------------------------------------------------------------------------------


class AddProductsState(StatesGroup):
    waiting_for_addp = State()


@dp.message_handler(commands=['addproduct'])
async def add_product_handler(message: types.Message):
    await message.reply("Введите информацию о продукте: Название, Цена, Категория, Бренд, Описание, Скидка,"
                        "Дата добавления, Дату окончания срока годности")
    await AddProductsState.waiting_for_addp.set()


@dp.message_handler(state=AddProductsState.waiting_for_addp)
async def handle_product_add(message: types.Message, state: FSMContext):
    # Разделяем информацию о продукте на отдельные поля
    if message.text == '/exit':
        await state.finish()
        await message.reply("Вы успешно покинули режим получения информации о категории.")
        return

    product_info = message.text.split(",")

    # Убеждаемся, что указаны все три поля
    if len(product_info) != 8:
        await message.reply("Пожалуйста, введите информацию о продукте в формате: Название, Цену, Категорию"
                            "Бренд, Описание, Скидку, Дату, Дату окончания срока годности")
        return

    # Получаем значения полей
    title, price, category_title, brand_title, description_, discount, when_came_date, expiration_date = map(str.strip,
                                                                                                             product_info)

    # Добавляем информацию о продукте в базу данных
    try:
        connection = psycopg2.connect(user="postgres",
                                      password="pass001",
                                      host="localhost",
                                      port="5432",
                                      database="dbtwo")

        cursor = connection.cursor()

        # Вставка записи в таблицу products
        cursor.execute("INSERT INTO products(title, price, category_title, brand_title, description_, "
                       "discount, when_came_date, expiration_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                       (title, price, category_title, brand_title, description_, discount, when_came_date,
                        expiration_date))

        connection.commit()
        cursor.close()
        connection.close()

        await message.reply("Продукт успешно добавлен в базу данных!")
    except (Exception, psycopg2.Error) as error:
        await message.reply(f"Произошла ошибка при добавлении продукта: {str(error)}")

    await state.finish()


# ----------------------------------------------------------------------------------------------------------------------


class AllProductsState(StatesGroup):
    waiting_for_allp = State()


@dp.message_handler(commands=['allproducts'])
async def all_products_handler(message: types.Message, state: FSMContext):
    if message.text == '/exit':
        await state.finish()
        await message.reply("Информация о продуктах.")
        return

    try:
        connection = psycopg2.connect(user="postgres",
                                      password="pass001",
                                      host="localhost",
                                      port="5432",
                                      database="dbtwo")

        cursor = connection.cursor()

        cursor.execute("SELECT * FROM all_products_view;")

        productsall = cursor.fetchall()

        if len(productsall) > 0:
            response = "Список всех продуктов: \n"
            for product in productsall:
                response += f"Название: {product[2]} \n UUID Продукта: {product[1]} \n ID Продукта: {product[0]} \n" \
                            f"Цена: {product[3]} \n Категория: {product[4]} \n Бренд: {product[5]} \n Описание: {product[6]} \n Скидка: {product[7]} \n"

            await message.reply(response)
        else:
            await message.reply("В базе данных нет продуктов!")

        cursor.close()
        connection.close()

    except (Exception, psycopg2.Error) as error:
        await message.reply(f"Произошла ошибка при получении списка продуктов: {str(error)}")

    await state.finish()


# ----------------------------------------------------------------------------------------------------------------------


class LatestProductsState(StatesGroup):
    waiting_for_latestp = State()


@dp.message_handler(commands=['latestproducts'])
async def latest_products_handler(message: types.Message, state: FSMContext):
    if message.text == '/exit':
        await state.finish()
        await message.reply("Вы успешно покинули режим получения последних продуктов.")
        return

    try:
        connection = psycopg2.connect(user="postgres",
                                      password="pass001",
                                      host="localhost",
                                      port="5432",
                                      database="dbtwo")

        cursor = connection.cursor()

        cursor.execute("SELECT * FROM latest_products;")

        latest_products = cursor.fetchall()

        if len(latest_products) > 0:
            response = "Список последних 10 продуктов:\n"
            for productlat in latest_products:
                response += f"Название: {productlat[2]} \n UUID Продукта: {productlat[1]} \n ID продукта: {productlat[0]} \n"

            await message.reply(response)
        else:
            await message.reply("В базе данных нет продуктов!")

        cursor.close()
        connection.close()

    except (Exception, psycopg2.Error) as error:
        await message.reply(f"Произошла ошибка при получении списка последних 10 продуктов: {str(error)}")

    await state.finish()


# ----------------------------------------------------------------------------------------------------------------------


class UUIDInfoState(StatesGroup):
    waiting_for_uuid = State()


@dp.message_handler(commands=['uuid_info'])
async def uuid_info_handler(message: types.Message):
    await message.reply("Введите UUID продукта для получения информации:")
    await UUIDInfoState.waiting_for_uuid.set()
    # dp.register_message_handler(handle_uuid_info, state=None)


@dp.message_handler(state=UUIDInfoState.waiting_for_uuid)
async def handle_uuid_info(message: types.Message, state: FSMContext):
    if message.text == '/exit':
        await state.finish()
        await message.reply("Вы успешно покинули режим получения информации о категории.")
        return

    uuid = message.text.strip()

    try:
        connection = psycopg2.connect(user="postgres",
                                      password="pass001",
                                      host="localhost",
                                      port="5432",
                                      database="dbtwo")
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM product_details WHERE product_uuid = %s", (uuid,))
        uuid_product = cursor.fetchone()

        if uuid_product:
            await message.reply(
                f"Информация о продукте с UUID {uuid}:\n\nID: {uuid_product[0]}\nUUID: {uuid_product[1]}"
                f"\nНазвание: {uuid_product[2]}\nЦена: {uuid_product[3]}\nКатегория: {uuid_product[4]}"
                f"\nБренд: {uuid_product[5]}\nОписание: {uuid_product[6]}\nСкидка: {uuid_product[7]}"
                f"\nДата: {uuid_product[8]}\nДата окончания срока годности: {uuid_product[9]}")
        else:
            await message.reply("Продукт с указанным UUID не найден в базе данных.")

        cursor.close()
        connection.close()
    except (Exception, psycopg2.Error) as error:
        await message.reply(f"Произошла ошибка при запросе информации о продукте: {str(error)}")

    await state.finish()


# ----------------------------------------------------------------------------------------------------------------------


class CategoryInfoState(StatesGroup):
    waiting_for_category = State()


@dp.message_handler(commands=['category_info'])
async def category_info_handler(message: types.Message):
    await message.reply("Введите категорию продукта для вывода информации")
    await CategoryInfoState.waiting_for_category.set()


@dp.message_handler(state=CategoryInfoState.waiting_for_category)
async def handle_category_info(message: types.Message, state: FSMContext):
    if message.text == '/exit':
        await state.finish()
        await message.reply("Вы успешно покинули режим получения информации о категории.")
        return

    category_title = message.text.strip()

    try:
        connection = psycopg2.connect(user="postgres",
                                      password="pass001",
                                      host="localhost",
                                      port="5432",
                                      database="dbtwo")

        cursor = connection.cursor()

        cursor.execute("SELECT title, price FROM products_by_category WHERE category_title = %s", (category_title,))

        products = cursor.fetchall()
        if not products:
            await message.reply(f"В категории '{category_title}' нет ни одного продукта.")
        else:
            reply = "Продукты в категории '{}':\n".format(category_title)
            for productinf in products:
                title, price = productinf
                reply += f"- {title}, Цена: {price}\n"
            await message.reply(reply)

        cursor.close()
        connection.close()

    except (Exception, psycopg2.Error) as error:
        await message.reply(f"Произошла ошибка при получении информации о категории: {str(error)}")

    await state.finish()


# ----------------------------------------------------------------------------------------------------------------------


class BrandInfoState(StatesGroup):
    waiting_for_brand = State()


@dp.message_handler(commands=['brand_info'])
async def brand_info_handler(message: types.Message):
    await message.reply("Введите бренд продукта для вывода информации")
    await BrandInfoState.waiting_for_brand.set()


@dp.message_handler(state=BrandInfoState.waiting_for_brand)
async def handle_brand_info(message: types.Message, state: FSMContext):
    if message.text == '/exit':
        await state.finish()
        await message.reply("Вы успешно покинули режим получения информации о бренде.")
        return

    brand_title = message.text.strip()

    try:
        connection = psycopg2.connect(user="postgres",
                                      password="pass001",
                                      host="localhost",
                                      port="5432",
                                      database="dbtwo")

        cursor = connection.cursor()

        cursor.execute("SELECT title, price FROM products_by_brands WHERE brand_title = %s", (brand_title,))

        products_brand = cursor.fetchall()
        if not products_brand:
            await message.reply(f"Нет ни одного продукта бренда '{brand_title}'.")
        else:
            reply = "Продукты бренда '{}':\n".format(brand_title)
            for productbr in products_brand:
                title, price = productbr
                reply += f"- {title}, Цена: {price}\n"
            await message.reply(reply)

        cursor.close()
        connection.close()

    except (Exception, psycopg2.Error) as error:
        await message.reply(f"Произошла ошибка при получении информации о бренде: {str(error)}")

    await state.finish()


# ----------------------------------------------------------------------------------------------------------------------


class UUIDDeleteState(StatesGroup):
    waiting_for_uuiddel = State()


@dp.message_handler(commands=['delete_by_uuid'])
async def uuid_delete_handler(message: types.Message):
    await message.reply("Введите UUID продукта:")
    await UUIDDeleteState.waiting_for_uuiddel.set()


@dp.message_handler(state=UUIDDeleteState.waiting_for_uuiddel)
async def handle_uuid_delete(message: types.Message, state: FSMContext):
    if message.text == '/exit':
        await state.finish()
        await message.reply("Вы успешно покинули режим получения информации о категории.")
        return

    uuid = message.text.strip()

    try:
        connection = psycopg2.connect(user="postgres",
                                      password="pass001",
                                      host="localhost",
                                      port="5432",
                                      database="dbtwo")
        cursor = connection.cursor()

        cursor.execute("DELETE FROM products WHERE product_uuid = %s RETURNING product_uuid", (uuid,))
        uuid_delete = cursor.fetchone()

        if uuid_delete:
            await message.reply("Продукт удален")

        else:
            await message.reply("Продукт с указанным UUID не найден в базе данных.")

        connection.commit()
        cursor.close()
        connection.close()
    except (Exception, psycopg2.Error) as error:
        await message.reply(f"Произошла ошибка при удалении продукта: {str(error)}")

    await state.finish()


# ----------------------------------------------------------------------------------------------------------------------


class UUIDUpdateState(StatesGroup):
    waiting_for_uuidupd = State()
    waiting_for_title = State()
    waiting_for_price = State()
    waiting_for_category = State()
    waiting_for_brand = State()


@dp.message_handler(commands=['update_by_uuid'])
async def uuid_update_handler(message: types.Message):
    await message.reply("Введите UUID продукта:")
    await UUIDUpdateState.waiting_for_uuidupd.set()


@dp.message_handler(state=UUIDUpdateState.waiting_for_uuidupd)
async def handle_uuid_update(message: types.Message, state: FSMContext):
    if message.text == '/exit':
        await state.finish()
        await message.reply("Вы успешно покинули режим обновления продукта по UUID.")
        return

    uuid = message.text.strip()
    await state.update_data(uuid=uuid)

    await message.reply("Введите новое название продукта:")
    await UUIDUpdateState.waiting_for_title.set()


@dp.message_handler(state=UUIDUpdateState.waiting_for_title)
async def handle_new_title(message: types.Message, state: FSMContext):
    new_title = message.text.strip()
    await state.update_data(new_title=new_title)

    await message.reply("Введите новую цену продукта:")
    await UUIDUpdateState.waiting_for_price.set()


@dp.message_handler(state=UUIDUpdateState.waiting_for_price)
async def handle_new_price(message: types.Message, state: FSMContext):
    new_price = message.text.strip()
    await state.update_data(new_price=new_price)

    await message.reply("Введите новую категорию продукта:")
    await UUIDUpdateState.waiting_for_category.set()


@dp.message_handler(state=UUIDUpdateState.waiting_for_category)
async def handle_new_category(message: types.Message, state: FSMContext):
    new_category = message.text.strip()
    await state.update_data(new_category=new_category)

    await message.reply("Введите новый бренд продукта:")
    await UUIDUpdateState.waiting_for_brand.set()


@dp.message_handler(state=UUIDUpdateState.waiting_for_brand)
async def handle_new_brand(message: types.Message, state: FSMContext):
    new_brand = message.text.strip()
    await state.update_data(new_brand=new_brand)

    data = await state.get_data()
    uuid = data.get('uuid')
    new_title = data.get('new_title')
    new_price = data.get('new_price')
    new_category = data.get('new_category')

    try:
        connection = psycopg2.connect(user="postgres",
                                      password="pass001",
                                      host="localhost",
                                      port="5432",
                                      database="dbtwo")

        cursor = connection.cursor()

        cursor.execute(
            "UPDATE products SET title = %s, price = %s, category_title = %s, brand_title = %s WHERE product_uuid = %s RETURNING product_uuid",
            (new_title, new_price, new_category, new_brand, uuid))

        if cursor.rowcount:
            await message.reply("Продукт успешно обновлен!")
        else:
            await message.reply(f"Продукт с UUID {uuid} не найден.")

        connection.commit()
        cursor.close()
        connection.close()
    except (Exception, psycopg2.Error) as error:
        await message.reply(f"Произошла ошибка при обновлении продукта: {str(error)}")

    await state.finish()


# ---------------------------------------------------------------------------------------------------------------------


class UserState(StatesGroup):
    entering_data = State()
    editing_data = State()
    editing_name = State()
    editing_phone = State()
    editing_adress = State()
    editing_email = State()


cursor = conn.cursor()


# Обработчик команды для входа в личный кабинет
@dp.message_handler(commands=['enter'])
async def start(message: types.Message):
    await message.answer("Для входа в личный кабинет введите ваш номер:")
    await UserState.entering_data.set()


# Обработчик ввода данных пользователя
@dp.message_handler(state=UserState.entering_data)
async def process_entering_data(message: types.Message, state: FSMContext):
    client_phone = message.text
    # Проверка наличия пользователя в базе данных по номеру телефона

    cursor.execute("SELECT * FROM clients WHERE client_phone = %s", (client_phone,))
    user_exists = cursor.fetchone()
    if user_exists:
        await message.answer(f"Вы вошли в личный кабинет. Ваши данные: \n"
                             f"Имя: {user_exists[2]}\n"
                             f"Номер телефона: {user_exists[3]}\n"
                             f"Email: {user_exists[4]}\n"
                             f"Адрес: {user_exists[5]}\n")
        # Добавить кнопку "Изменить данные"
    else:
        await message.answer("Пользователь не найден")
    await state.finish()

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("Изменить данные"))
    await message.answer("Вы вошли в личный кабинет", reply_markup=keyboard)


# Обработчик кнопки "Изменить данные"
@dp.message_handler(lambda message: message.text == 'Изменить данные')
async def editing_data(message: types.Message):
    await message.answer("Введите ваше новое имя:")
    await UserState.editing_name.set()


# Обработчик ввода нового имени
@dp.message_handler(state=UserState.editing_name)
async def process_editing_name(message: types.Message, state: FSMContext):
    # Сохраняем введенное имя в состоянии пользователя
    await state.update_data(editing_name=message.text)
    await message.answer("Теперь введите ваш новый адрес:")
    await UserState.editing_adress.set()


# Обработчик ввода нового адреса
@dp.message_handler(state=UserState.editing_adress)
async def process_editing_address(message: types.Message, state: FSMContext):
    # Обновляем данные в состоянии пользователя
    user_data = await state.get_data()
    user_data['editing_adress'] = message.text
    await state.update_data(user_data)
    await message.answer("Теперь введите ваш новый номер телефона:")
    await UserState.editing_phone.set()


# Обработчик ввода нового номера телефона
@dp.message_handler(state=UserState.editing_phone)
async def process_editing_phone(message: types.Message, state: FSMContext):
    # Обновляем данные в состоянии пользователя
    user_data = await state.get_data()
    user_data['editing_phone'] = message.text
    await state.update_data(user_data)
    await message.answer("И, наконец, введите ваш новый email:")
    await UserState.editing_email.set()


# Обработчик ввода нового email и выполнение обновления данных
@dp.message_handler(state=UserState.editing_email)
async def process_editing_email(message: types.Message, state: FSMContext):
    # Получаем все введенные данные из состояния пользователя
    editing_data = await state.get_data()
    editing_name = editing_data['editing_name']
    editing_address = editing_data['editing_adress']
    editing_phone = editing_data['editing_phone']
    editing_email = message.text

    # Получаем id пользователя
    user_data = await state.get_data()
    client_id = user_data.get('client_id')

    # Обновление данных в бд
    cursor.execute(
        "UPDATE clients SET client_name = %s, client_phone = %s, client_email = %s, client_adress = %s WHERE client_id = %s",
        (editing_name, editing_phone, editing_email, editing_address, client_id))

    conn.commit()

    # Вывод сообщения "данные изменены"
    await message.answer("Данные изменены")

    # Закрываем состояние пользователя
    await state.finish()
# ----------------------------------------------------------------------------------------------------------------------

# Запуск бота


if __name__ == "__main__":
    # Установка соединения с базой данных
    conn = psycopg2.connect(database="dbtwo", user="postgres", password="pass001", host="localhost",
                            port="5432")

    # Создание объекта курсора для выполнения операций с базой данных
    cur = conn.cursor()

    # Создание и запуск пула соединений PostgreSQL
    executor = aiogram.executor.Executor(dp)
    executor.start_polling()
