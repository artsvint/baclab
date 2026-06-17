import pymysql
from werkzeug.security import generate_password_hash


# -----------------------------------------------------------------------------
# Подключение к БД
# -----------------------------------------------------------------------------
# В этом файле находятся все запросы к базе данных.
# База должна быть предварительно создана скриптом: sql/init_baclab_mysql84.sql


def connect_db():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="dreddred",
        database="baclab_lis",
        port=3306,
        cursorclass=pymysql.cursors.DictCursor
    )


# -----------------------------------------------------------------------------
# Базовые функции выполнения запросов
# -----------------------------------------------------------------------------


def fetch_all(sql, params=None):
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()
    finally:
        connection.close()


def fetch_one(sql, params=None):
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchone()
    finally:
        connection.close()


def execute(sql, params=None):
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params or ())
            connection.commit()
            return cursor.lastrowid
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def execute_many(sql, values):
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.executemany(sql, values)
            connection.commit()
            return cursor.rowcount
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


# -----------------------------------------------------------------------------
# Служебные функции
# -----------------------------------------------------------------------------


def _none_if_empty(value):
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


# -----------------------------------------------------------------------------
# Авторизация и пользователи
# -----------------------------------------------------------------------------


def count_users():
    row = fetch_one("SELECT COUNT(*) AS cnt FROM APP_USER")
    return row["cnt"] if row else 0


def get_roles():
    return fetch_all("SELECT ROLE_ID, ROLE_CODE, ROLE_NAME FROM ROLE ORDER BY ROLE_ID")


def get_role_by_code(role_code):
    return fetch_one(
        "SELECT ROLE_ID, ROLE_CODE, ROLE_NAME FROM ROLE WHERE ROLE_CODE = %s",
        (role_code,)
    )


def get_user_by_username(username):
    return fetch_one(
        """
        SELECT
            u.USER_ID,
            u.USERNAME,
            u.PASSWORD_HASH,
            u.FULL_NAME,
            u.IS_ACTIVE,
            r.ROLE_ID,
            r.ROLE_CODE,
            r.ROLE_NAME
        FROM APP_USER u
        JOIN ROLE r ON r.ROLE_ID = u.ROLE_ID
        WHERE u.USERNAME = %s
        """,
        (username,)
    )


def get_user_by_id(user_id):
    return fetch_one(
        """
        SELECT
            u.USER_ID,
            u.USERNAME,
            u.FULL_NAME,
            u.IS_ACTIVE,
            r.ROLE_ID,
            r.ROLE_CODE,
            r.ROLE_NAME
        FROM APP_USER u
        JOIN ROLE r ON r.ROLE_ID = u.ROLE_ID
        WHERE u.USER_ID = %s
        """,
        (user_id,)
    )


def create_user(username, password, full_name, role_code="viewer"):
    role = get_role_by_code(role_code)
    if not role:
        raise ValueError(f"Роль {role_code} не найдена в таблице ROLE")

    password_hash = generate_password_hash(password)
    return execute(
        """
        INSERT INTO APP_USER (USERNAME, PASSWORD_HASH, FULL_NAME, ROLE_ID, IS_ACTIVE)
        VALUES (%s, %s, %s, %s, TRUE)
        """,
        (username, password_hash, full_name, role["ROLE_ID"])
    )


def get_users():
    return fetch_all(
        """
        SELECT
            u.USER_ID,
            u.USERNAME,
            u.FULL_NAME,
            u.IS_ACTIVE,
            u.CREATED_AT,
            r.ROLE_ID,
            r.ROLE_CODE,
            r.ROLE_NAME
        FROM APP_USER u
        JOIN ROLE r ON r.ROLE_ID = u.ROLE_ID
        ORDER BY u.CREATED_AT DESC, u.USER_ID DESC
        """
    )


def update_user_role(user_id, role_id):
    return execute(
        "UPDATE APP_USER SET ROLE_ID = %s WHERE USER_ID = %s",
        (role_id, user_id)
    )


def set_user_active(user_id, is_active):
    return execute(
        "UPDATE APP_USER SET IS_ACTIVE = %s WHERE USER_ID = %s",
        (bool(is_active), user_id)
    )


# -----------------------------------------------------------------------------
# Справочники
# -----------------------------------------------------------------------------


def get_dictionaries():
    return {
        "mdr": fetch_all("SELECT ID, TUB_MULTIDRUG_RESISTENCE FROM MDR ORDER BY ID"),
        "gdu": fetch_all("SELECT GDU_ID, GDU_DESCRIPTION FROM GDU ORDER BY GDU_ID"),
        "labs": fetch_all("SELECT IDMU, SH_LNAME FROM LABS ORDER BY SH_LNAME"),
        "mu": get_medical_organizations(),
        "mu_offices_kkptd": get_mu_offices(13812),
        "test_codes": fetch_all("SELECT ID, S_CODE, NAME, TEST_ATTRIBUTE FROM TEST_CODE ORDER BY S_CODE"),
        "matters": fetch_all("SELECT ID, MATTER FROM MATTERS ORDER BY MATTER"),
        "matter_origin": fetch_all("SELECT ID, MATTER_ORIGIN FROM MATTER_ORIGIN ORDER BY MATTER_ORIGIN"),
        "bact_excretion": fetch_all("SELECT ID, BACT_EXCRETION FROM BACT_EXCRETION ORDER BY ID"),
        "drug_resistance": fetch_all("SELECT ID, DRUG_RESISTANCE, DESCRIPTION FROM DRUG_RESISTANCE ORDER BY ID"),
        "drugs": fetch_all("SELECT UniqueID, drug_code, short_name FROM DRUGS ORDER BY UniqueID"),
    }


def get_medical_organizations():
    return fetch_all(
        """
        SELECT IDMU, SH_LNAME, MU, MUFL
        FROM MU
        WHERE FLAG_MU = 1
        ORDER BY SH_LNAME
        """
    )


def get_mu_offices(parent_mu_id):
    return fetch_all(
        """
        SELECT IDMU, SH_LNAME, MU, MUFL, IDOFFICE
        FROM MU
        WHERE IDOFFICE = %s
        ORDER BY SH_LNAME
        """,
        (parent_mu_id,)
    )


def get_test_values_by_test_code(test_code_id):
    return fetch_all(
        """
        SELECT tv.VALUE_ID, tv.TEST_VALUE
        FROM TEST_VALUES tv
        JOIN TEST_CODE tc ON tc.TEST_ATTRIBUTE = tv.TEST_ATTRIBUTE
        WHERE tc.ID = %s
        ORDER BY tv.TEST_VALUE
        """,
        (test_code_id,)
    )


# -----------------------------------------------------------------------------
# Пациенты
# -----------------------------------------------------------------------------


def get_patient_count():
    row = fetch_one("SELECT COUNT(*) AS cnt FROM PATIENT WHERE IS_DELETED = FALSE")
    return row["cnt"] if row else 0


def get_patients(search="", limit=100, offset=0):
    search = (search or "").strip()
    params = []
    where = "WHERE p.IS_DELETED = FALSE"

    if search:
        where += " AND (p.PATIENT_LN LIKE %s OR p.PATIENT_FN LIKE %s OR p.PATIENT_SN LIKE %s OR p.SNILS LIKE %s)"
        like_value = f"%{search}%"
        params.extend([like_value, like_value, like_value, like_value])

    params.extend([int(limit), int(offset)])

    return fetch_all(
        f"""
        SELECT
            p.PATIENT_ID,
            p.PATIENT_LN,
            p.PATIENT_FN,
            p.PATIENT_SN,
            p.BIRTHDATE,
            p.SNILS,
            p.PATIENT_VV,
            p.ACCOUNTING_DAY,
            p.PATIENT_NOTES,
            m.TUB_MULTIDRUG_RESISTENCE,
            g.GDU_DESCRIPTION
        FROM PATIENT p
        LEFT JOIN MDR m ON m.ID = p.MDR
        LEFT JOIN GDU g ON g.GDU_ID = p.GDU
        {where}
        ORDER BY p.PATIENT_LN, p.PATIENT_FN, p.PATIENT_SN
        LIMIT %s OFFSET %s
        """,
        tuple(params)
    )


def get_patient(patient_id):
    return fetch_one(
        """
        SELECT
            p.*,
            m.TUB_MULTIDRUG_RESISTENCE,
            g.GDU_DESCRIPTION
        FROM PATIENT p
        LEFT JOIN MDR m ON m.ID = p.MDR
        LEFT JOIN GDU g ON g.GDU_ID = p.GDU
        WHERE p.PATIENT_ID = %s AND p.IS_DELETED = FALSE
        """,
        (patient_id,)
    )


def create_patient(data):
    return execute(
        """
        INSERT INTO PATIENT (
            PATIENT_LN, PATIENT_FN, PATIENT_SN, BIRTHDATE, SNILS,
            PATIENT_VV, ACCOUNTING_DAY, MDR, GDU, PATIENT_NOTES
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            data["PATIENT_LN"],
            data["PATIENT_FN"],
            _none_if_empty(data.get("PATIENT_SN")),
            _none_if_empty(data.get("BIRTHDATE")),
            _none_if_empty(data.get("SNILS")),
            bool(data.get("PATIENT_VV")),
            _none_if_empty(data.get("ACCOUNTING_DAY")),
            _none_if_empty(data.get("MDR")),
            _none_if_empty(data.get("GDU")),
            _none_if_empty(data.get("PATIENT_NOTES")),
        )
    )


def update_patient(patient_id, data):
    execute(
        """
        UPDATE PATIENT
        SET
            PATIENT_LN = %s,
            PATIENT_FN = %s,
            PATIENT_SN = %s,
            BIRTHDATE = %s,
            SNILS = %s,
            PATIENT_VV = %s,
            ACCOUNTING_DAY = %s,
            MDR = %s,
            GDU = %s,
            PATIENT_NOTES = %s
        WHERE PATIENT_ID = %s AND IS_DELETED = FALSE
        """,
        (
            data["PATIENT_LN"],
            data["PATIENT_FN"],
            _none_if_empty(data.get("PATIENT_SN")),
            _none_if_empty(data.get("BIRTHDATE")),
            _none_if_empty(data.get("SNILS")),
            bool(data.get("PATIENT_VV")),
            _none_if_empty(data.get("ACCOUNTING_DAY")),
            _none_if_empty(data.get("MDR")),
            _none_if_empty(data.get("GDU")),
            _none_if_empty(data.get("PATIENT_NOTES")),
            patient_id,
        )
    )


def delete_patient(patient_id):
    execute(
        "UPDATE PATIENT SET IS_DELETED = TRUE WHERE PATIENT_ID = %s",
        (patient_id,)
    )


# -----------------------------------------------------------------------------
# Анализы / исследования
# -----------------------------------------------------------------------------


def get_analysis_count():
    row = fetch_one("SELECT COUNT(*) AS cnt FROM TEST WHERE IS_DELETED = FALSE")
    return row["cnt"] if row else 0


def get_tests_by_patient(patient_id):
    return fetch_all(
        """
        SELECT *
        FROM V_ANALYSIS_LIST
        WHERE PATIENT_ID = %s
        ORDER BY TEST_DATE DESC, TEST_ID DESC
        """,
        (patient_id,)
    )


def get_test(test_id):
    return fetch_one(
        """
        SELECT
            t.*,
            tc.TEST_ATTRIBUTE
        FROM TEST t
        JOIN TEST_CODE tc ON tc.ID = t.TEST_CODE
        WHERE t.TEST_ID = %s AND t.IS_DELETED = FALSE
        """,
        (test_id,)
    )


def get_abg_results(test_id):
    rows = fetch_all(
        """
        SELECT
            d.drug_code AS short_name,
            ar.RESISTANCE_ID,
            dr.DRUG_RESISTANCE
        FROM TEST_ISOLATE ti
        JOIN ANTIBIOGRAM a ON a.ISOLATE_ID = ti.ISOLATE_ID
        JOIN ANTIBIOGRAM_RESULT ar ON ar.ABG_ID = a.ABG_ID
        JOIN DRUGS d ON d.UniqueID = ar.DRUG_ID
        LEFT JOIN DRUG_RESISTANCE dr ON dr.ID = ar.RESISTANCE_ID
        WHERE ti.TEST_ID = %s
        ORDER BY d.UniqueID
        """,
        (test_id,)
    )
    return {row["short_name"]: row for row in rows}


def create_test(data, abg_values=None):
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO TEST (
                    PATIENT_ID, LAB_ID, MU_ID, MU_OFFICE_ID, MATTER_ORIGIN, TEST_NUMBER,
                    TEST_DATE, TEST_CODE, MATTER_ID, BACT_EXCRETION,
                    TEST_RESULT, GROWTH_DAY, GROWTH_RATE, ABG_DATE,
                    TEST_NOTES, CREATED_BY, UPDATED_BY
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    data["PATIENT_ID"],
                    _none_if_empty(data.get("LAB_ID")),
                    _none_if_empty(data.get("MU_ID")),
                    _none_if_empty(data.get("MU_OFFICE_ID")),
                    _none_if_empty(data.get("MATTER_ORIGIN")),
                    data["TEST_NUMBER"],
                    data["TEST_DATE"],
                    data["TEST_CODE"],
                    _none_if_empty(data.get("MATTER_ID")),
                    _none_if_empty(data.get("BACT_EXCRETION")),
                    _none_if_empty(data.get("TEST_RESULT")),
                    _none_if_empty(data.get("GROWTH_DAY")),
                    _none_if_empty(data.get("GROWTH_RATE")),
                    _none_if_empty(data.get("ABG_DATE")),
                    _none_if_empty(data.get("TEST_NOTES")),
                    _none_if_empty(data.get("USER_ID")),
                    _none_if_empty(data.get("USER_ID")),
                )
            )
            test_id = cursor.lastrowid
            _save_abg_results_with_cursor(cursor, test_id, abg_values or {}, data.get("ABG_DATE"))
            connection.commit()
            return test_id
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def update_test(test_id, data, abg_values=None):
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE TEST
                SET
                    LAB_ID = %s,
                    MU_ID = %s,
                    MU_OFFICE_ID = %s,
                    MATTER_ORIGIN = %s,
                    TEST_NUMBER = %s,
                    TEST_DATE = %s,
                    TEST_CODE = %s,
                    MATTER_ID = %s,
                    BACT_EXCRETION = %s,
                    TEST_RESULT = %s,
                    GROWTH_DAY = %s,
                    GROWTH_RATE = %s,
                    ABG_DATE = %s,
                    TEST_NOTES = %s,
                    UPDATED_BY = %s
                WHERE TEST_ID = %s AND IS_DELETED = FALSE
                """,
                (
                    _none_if_empty(data.get("LAB_ID")),
                    _none_if_empty(data.get("MU_ID")),
                    _none_if_empty(data.get("MU_OFFICE_ID")),
                    _none_if_empty(data.get("MATTER_ORIGIN")),
                    data["TEST_NUMBER"],
                    data["TEST_DATE"],
                    data["TEST_CODE"],
                    _none_if_empty(data.get("MATTER_ID")),
                    _none_if_empty(data.get("BACT_EXCRETION")),
                    _none_if_empty(data.get("TEST_RESULT")),
                    _none_if_empty(data.get("GROWTH_DAY")),
                    _none_if_empty(data.get("GROWTH_RATE")),
                    _none_if_empty(data.get("ABG_DATE")),
                    _none_if_empty(data.get("TEST_NOTES")),
                    _none_if_empty(data.get("USER_ID")),
                    test_id,
                )
            )
            _save_abg_results_with_cursor(cursor, test_id, abg_values or {}, data.get("ABG_DATE"))
            connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def delete_test(test_id):
    execute(
        "UPDATE TEST SET IS_DELETED = TRUE WHERE TEST_ID = %s",
        (test_id,)
    )


def _save_abg_results_with_cursor(cursor, test_id, abg_values, abg_date=None):
    # Если антибиотикограмма не заполнена, удаляем старые значения и ничего не создаём.
    has_values = any(str(value).strip() for value in abg_values.values() if value is not None)

    cursor.execute(
        """
        SELECT a.ABG_ID
        FROM TEST_ISOLATE ti
        JOIN ANTIBIOGRAM a ON a.ISOLATE_ID = ti.ISOLATE_ID
        WHERE ti.TEST_ID = %s
        ORDER BY a.ABG_ID
        LIMIT 1
        """,
        (test_id,)
    )
    abg = cursor.fetchone()

    if abg:
        cursor.execute(
            "DELETE FROM ANTIBIOGRAM_RESULT WHERE ABG_ID = %s",
            (abg["ABG_ID"],)
        )

    if not has_values:
        return

    cursor.execute(
        "SELECT ISOLATE_ID FROM TEST_ISOLATE WHERE TEST_ID = %s ORDER BY ISOLATE_ID LIMIT 1",
        (test_id,)
    )
    isolate = cursor.fetchone()

    if isolate:
        isolate_id = isolate["ISOLATE_ID"]
    else:
        cursor.execute(
            """
            INSERT INTO TEST_ISOLATE (TEST_ID, MICROORGANISM_NAME, ISOLATE_DATE, GROWTH_RATE)
            VALUES (%s, 'Микобактерии туберкулеза', %s, NULL)
            """,
            (test_id, _none_if_empty(abg_date))
        )
        isolate_id = cursor.lastrowid

    if abg:
        abg_id = abg["ABG_ID"]
        cursor.execute(
            "UPDATE ANTIBIOGRAM SET ABG_DATE = %s WHERE ABG_ID = %s",
            (_none_if_empty(abg_date), abg_id)
        )
    else:
        cursor.execute(
            "INSERT INTO ANTIBIOGRAM (ISOLATE_ID, ABG_DATE) VALUES (%s, %s)",
            (isolate_id, _none_if_empty(abg_date))
        )
        abg_id = cursor.lastrowid

    for short_name, resistance_id in abg_values.items():
        if _none_if_empty(resistance_id) is None:
            continue
        cursor.execute(
            """
            SELECT UniqueID
            FROM DRUGS
            WHERE UPPER(drug_code) = UPPER(%s)
               OR UPPER(short_name) = UPPER(%s)
            LIMIT 1
            """,
            (short_name, short_name)
        )
        drug = cursor.fetchone()
        if not drug:
            continue
        cursor.execute(
            """
            INSERT INTO ANTIBIOGRAM_RESULT (ABG_ID, DRUG_ID, RESISTANCE_ID)
            VALUES (%s, %s, %s)
            """,
            (abg_id, drug["UniqueID"], resistance_id)
        )


# -----------------------------------------------------------------------------
# Отчёты
# -----------------------------------------------------------------------------


def get_patient_report(patient_id):
    patient = get_patient(patient_id)
    tests = get_tests_by_patient(patient_id)
    return patient, tests


# -----------------------------------------------------------------------------
# Журнал действий
# -----------------------------------------------------------------------------


def write_audit_log(user_id, action_code, entity_name, entity_id=None, action_text=None):
    return execute(
        """
        INSERT INTO AUDIT_LOG (USER_ID, ACTION_CODE, ENTITY_NAME, ENTITY_ID, ACTION_TEXT)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (_none_if_empty(user_id), action_code, entity_name, _none_if_empty(entity_id), action_text)
    )

# -----------------------------------------------------------------------------
# Административное редактирование справочников
# -----------------------------------------------------------------------------
# Настройки справочников используются только как белый список таблиц и столбцов.
# Имена таблиц и полей не берутся из пользовательского ввода напрямую.

REFERENCE_TABLES = {
    "mdr": {
        "title": "Лекарственная устойчивость",
        "table": "MDR",
        "pk": "ID",
        "fields": [
            {"name": "TUB_MULTIDRUG_RESISTENCE", "label": "Лекарственная устойчивость", "required": True},
        ],
    },
    "gdu": {
        "title": "Группы диспансерного учета",
        "table": "GDU",
        "pk": "GDU_ID",
        "fields": [
            {"name": "GDU_DESCRIPTION", "label": "ГДУ", "required": True},
        ],
    },
    "labs": {
        "title": "Лаборатории",
        "table": "LABS",
        "pk": "IDMU",
        "fields": [
            {"name": "FLAG_MU", "label": "Флаг МО"},
            {"name": "OFFICE", "label": "Офис"},
            {"name": "IDOFFICE", "label": "ID офиса"},
            {"name": "MU", "label": "Медучреждение"},
            {"name": "IDLPU", "label": "ID ЛПУ"},
            {"name": "IDADRES", "label": "ID адреса"},
            {"name": "IDTMU", "label": "ID типа МО"},
            {"name": "MUFL", "label": "Филиал"},
            {"name": "SH_LNAME", "label": "Краткое наименование", "required": True},
        ],
    },
    "mu": {
        "title": "Медицинские учреждения",
        "table": "MU",
        "pk": "IDMU",
        "fields": [
            {"name": "FLAG_MU", "label": "Флаг МО"},
            {"name": "OFFICE", "label": "Офис"},
            {"name": "IDOFFICE", "label": "ID офиса"},
            {"name": "MU", "label": "Медучреждение"},
            {"name": "IDLPU", "label": "ID ЛПУ"},
            {"name": "IDADRES", "label": "ID адреса"},
            {"name": "IDTMU", "label": "ID типа МО"},
            {"name": "MUFL", "label": "Филиал"},
            {"name": "SH_LNAME", "label": "Краткое наименование", "required": True},
        ],
    },
    "test_attribute": {
        "title": "Атрибуты исследований",
        "table": "TEST_ATTRIBUTE",
        "pk": "ID",
        "fields": [
            {"name": "TEST_ATTRIBUTE", "label": "Атрибут исследования", "required": True},
        ],
    },
    "test_values": {
        "title": "Значения исследований",
        "table": "TEST_VALUES",
        "pk": "VALUE_ID",
        "fields": [
            {
                "name": "TEST_ATTRIBUTE",
                "label": "Атрибут исследования",
                "required": True,
                "type": "select",
                "options_table": "TEST_ATTRIBUTE",
                "option_pk": "ID",
                "option_label": "TEST_ATTRIBUTE",
            },
            {"name": "TEST_VALUE", "label": "Значение результата", "required": True},
        ],
    },
    "test_code": {
        "title": "Исследования",
        "table": "TEST_CODE",
        "pk": "ID",
        "fields": [
            {"name": "S_CODE", "label": "Код исследования", "required": True},
            {"name": "NAME", "label": "Наименование", "required": True},
            {
                "name": "TEST_ATTRIBUTE",
                "label": "Атрибут исследования",
                "required": True,
                "type": "select",
                "options_table": "TEST_ATTRIBUTE",
                "option_pk": "ID",
                "option_label": "TEST_ATTRIBUTE",
            },
        ],
    },
    "matters": {
        "title": "Лабораторные материалы",
        "table": "MATTERS",
        "pk": "ID",
        "fields": [
            {"name": "MATTER", "label": "Материал", "required": True},
        ],
    },
    "matter_origin": {
        "title": "Происхождение материала",
        "table": "MATTER_ORIGIN",
        "pk": "ID",
        "fields": [
            {"name": "MATTER_ORIGIN", "label": "Происхождение материала", "required": True},
        ],
    },
    "bact_excretion": {
        "title": "Бактериовыделение",
        "table": "BACT_EXCRETION",
        "pk": "ID",
        "fields": [
            {"name": "BACT_EXCRETION", "label": "Бактериовыделение", "required": True},
        ],
    },
    "drug_resistance": {
        "title": "Варианты чувствительности к антибиотику",
        "table": "DRUG_RESISTANCE",
        "pk": "ID",
        "fields": [
            {"name": "DRUG_RESISTANCE", "label": "Значение", "required": True},
            {"name": "DESCRIPTION", "label": "Описание"},
        ],
    },
    "drugs": {
        "title": "Противотуберкулезные препараты",
        "table": "DRUGS",
        "pk": "UniqueID",
        "fields": [
            {"name": "drug_code", "label": "Код препарата", "required": True},
            {"name": "short_name", "label": "Краткое название", "required": True},
        ],
    },
}


def _quote_identifier(identifier):
    return "`" + identifier.replace("`", "``") + "`"


def get_reference_config(table_key):
    return REFERENCE_TABLES.get(table_key)


def get_reference_table_list():
    return [
        {"key": key, "title": config["title"]}
        for key, config in REFERENCE_TABLES.items()
    ]


def get_reference_form_options(table_key):
    config = get_reference_config(table_key)
    if not config:
        raise ValueError("Неизвестный справочник.")

    result = {}
    for field in config["fields"]:
        if field.get("type") != "select":
            continue
        result[field["name"]] = fetch_all(
            f"""
            SELECT
                {_quote_identifier(field['option_pk'])} AS option_id,
                {_quote_identifier(field['option_label'])} AS option_label
            FROM {_quote_identifier(field['options_table'])}
            ORDER BY {_quote_identifier(field['option_label'])}
            """
        )
    return result


def get_reference_rows(table_key):
    config = get_reference_config(table_key)
    if not config:
        raise ValueError("Неизвестный справочник.")

    table = _quote_identifier(config["table"])
    pk = _quote_identifier(config["pk"])
    select_columns = [f"t.{pk} AS {pk}"]
    joins = []

    for index, field in enumerate(config["fields"]):
        field_name = field["name"]
        field_sql = _quote_identifier(field_name)
        select_columns.append(f"t.{field_sql} AS {field_sql}")

        if field.get("type") == "select":
            alias = f"opt{index}"
            joins.append(
                f"LEFT JOIN {_quote_identifier(field['options_table'])} {alias} "
                f"ON {alias}.{_quote_identifier(field['option_pk'])} = t.{field_sql}"
            )
            select_columns.append(
                f"{alias}.{_quote_identifier(field['option_label'])} AS {_quote_identifier(field_name + '__display')}"
            )

    sql = f"""
        SELECT {', '.join(select_columns)}
        FROM {table} t
        {' '.join(joins)}
        ORDER BY t.{pk}
    """
    return fetch_all(sql)


def get_reference_row(table_key, record_id):
    config = get_reference_config(table_key)
    if not config:
        raise ValueError("Неизвестный справочник.")

    return fetch_one(
        f"SELECT * FROM {_quote_identifier(config['table'])} WHERE {_quote_identifier(config['pk'])} = %s",
        (record_id,)
    )


def _reference_values_from_form(config, form_data):
    values = {}
    for field in config["fields"]:
        name = field["name"]
        value = form_data.get(name)
        if isinstance(value, str):
            value = value.strip()
        if field.get("required") and not value:
            raise ValueError(f"Заполните поле: {field['label']}.")
        values[name] = _none_if_empty(value)
    return values


def create_reference_row(table_key, form_data):
    config = get_reference_config(table_key)
    if not config:
        raise ValueError("Неизвестный справочник.")

    values = _reference_values_from_form(config, form_data)
    columns = list(values.keys())
    placeholders = ", ".join(["%s"] * len(columns))
    sql = f"""
        INSERT INTO {_quote_identifier(config['table'])}
        ({', '.join(_quote_identifier(column) for column in columns)})
        VALUES ({placeholders})
    """
    return execute(sql, tuple(values[column] for column in columns))


def update_reference_row(table_key, record_id, form_data):
    config = get_reference_config(table_key)
    if not config:
        raise ValueError("Неизвестный справочник.")

    values = _reference_values_from_form(config, form_data)
    assignments = ", ".join(f"{_quote_identifier(column)} = %s" for column in values.keys())
    sql = f"""
        UPDATE {_quote_identifier(config['table'])}
        SET {assignments}
        WHERE {_quote_identifier(config['pk'])} = %s
    """
    execute(sql, tuple(values[column] for column in values.keys()) + (record_id,))


def delete_reference_row(table_key, record_id):
    config = get_reference_config(table_key)
    if not config:
        raise ValueError("Неизвестный справочник.")

    execute(
        f"DELETE FROM {_quote_identifier(config['table'])} WHERE {_quote_identifier(config['pk'])} = %s",
        (record_id,)
    )
