# ЛИС «Картотека» для бактериологической лаборатории

Веб-сервис на Flask для учета пациентов, бактериологических исследований, справочников и антибиотикограмм.

 
- Доступ к системе закрыт для неавторизованных пользователей.
- После выхода пользователь перенаправляется на страницу входа/регистрации.
 
## Состав проекта

```text
baclab_lis_flask/
├── app.py
├── config.py
├── db.py
├── requirements.txt
├── routes/
│   ├── auth_routes.py
│   ├── main_routes.py
│   ├── patient_routes.py
│   ├── analysis_routes.py
│   ├── report_routes.py
│   ├── user_routes.py
│   └── reference_routes.py
├── templates/
│   ├── base.html
│   ├── includes/
│   │   ├── header.html
│   │   ├── footer.html
│   │   └── auth_modals.html
│   └── pages/
│       ├── auth.html
│       ├── index.html
│       ├── references.html
│       ├── patient_form.html
│       ├── test_form.html
│       ├── patient_report.html
│       └── users.html
├── static/
│   ├── css/style.css
│   └── js/main.js

```

## Запуск

1. Создать и заполнить БД:
 
2. Установить зависимости:

```bash
pip install -r requirements.txt
```

3. Запустить приложение:

```bash
python app.py
```

4. Открыть в браузере:

```text
http://127.0.0.1:5000
```

## Доступ

Админ: admin | 123123
## Подключение к БД

Файл подключения и все SQL-запросы находятся в `db.py`.

Для уже созданной ранее базы после обновления проекта выполните:

```bash
mysql -u root -p < sql/migration_mu_office.sql
```
 