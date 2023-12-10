CREATE EXTENSION IF NOT EXISTS "uuid-ossp";



CREATE TABLE clients (
    client_id SERIAL PRIMARY KEY,
    client_chat_id UUID DEFAULT uuid_generate_v4() UNIQUE,
    client_name VARCHAR(255), 
    client_phone VARCHAR(255), 
    client_email VARCHAR(255),
    client_adress TEXT
);



CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    title VARCHAR(255),
    price INT,
    category_title VARCHAR(255),
    brand_title VARCHAR(255),
    description_ TEXT,
    discount INT,
    when_came_date DATE,
    expiration_date DATE
);



CREATE TABLE products_categories_brands (
    category_title VARCHAR,
    brand_title VARCHAR,
    FOREIGN KEY (category_title) REFERENCES categories(category_title),
    FOREIGN KEY (brand_title) REFERENCES brand(brand_title)
);



CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    category_title VARCHAR(255) UNIQUE
);



CREATE TABLE brand (
    brand_id SERIAL PRIMARY KEY,
    brand_title VARCHAR(255) UNIQUE
);



CREATE TABLE cart (
    cart_id SERIAL PRIMARY KEY,
    user_id INT,
    datetime_created DATE, 
    last_ordered DATE,
    product_name VARCHAR(40)
);



CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    user_id INT,
    datetime_created DATE
);



CREATE OR REPLACE VIEW all_products_view AS
SELECT * FROM products;


CREATE OR REPLACE VIEW latest_products AS
SELECT * FROM products
ORDER BY when_came_date DESC
LIMIT 10;


CREATE VIEW products_by_category AS
SELECT * 
FROM products;


CREATE VIEW products_by_brands AS
SELECT * 
FROM products;


CREATE VIEW product_details AS
SELECT product_id, product_uuid, title, price, brand_title, description_, discount, when_came_date, expiration_date
FROM products;

CREATE OR REPLACE VIEW deleted_by_uuid_view AS
SELECT * FROM products;



CREATE INDEX product_title_index ON products(title);

CREATE INDEX client_email_index ON clients(client_email);

CREATE INDEX brand_index ON brand(brand_title);

CREATE INDEX order_index ON orders(user_id);

