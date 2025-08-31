# app.py
import streamlit as st
import pandas as pd
from utils.db_connection import (
    get_mysql_schema,
    list_databases,
    list_tables,
    get_table_columns,
    fetch_table,
    run_select,
    insert_row,
    delete_rows,
    execute_update,
)

st.set_page_config(page_title="Cricket DB • CRUD", layout="wide")
st.title("🛠️ CRUD Operations")
st.caption("Create, Read, Update, Delete Player Records (MySQL via Streamlit)")

# -------------------------------
# 1) Connection details on MAIN TAB
# -------------------------------
st.header("🔌 MySQL Connection")

host = st.text_input("Host", value="localhost")
user = st.text_input("User", value="root")
passwd = st.text_input("Password", type="password")

if st.button("Connect & Discover Databases"):
    try:
        schema = get_mysql_schema(host, user, passwd)
        st.session_state["schema"] = schema
        st.success(f"✅ Connected. Found {len(schema)} databases.")
    except Exception as e:
        st.error(f"❌ Failed: {e}")

schema = st.session_state.get("schema", None)

st.divider()

# -------------------------------
# 2) Choose database & table
# -------------------------------
if schema:
    st.header("📂 Select Database & Table")

    dbs = sorted(schema.keys())
    database = st.selectbox("Choose Database", dbs, index=max(0, dbs.index("cricbuzz")) if "cricbuzz" in dbs else 0)

    tables = sorted(schema[database]["tables"].keys())
    default_table = "trending_players" if "trending_players" in tables else ("player_squad" if "player_squad" in tables else tables[0] if tables else "")
    table = st.selectbox("Choose Table", tables, index=max(0, tables.index(default_table)) if tables else 0)

    st.divider()

    # -------------------------------
    # 3) View / Read Table as DataFrame
    # -------------------------------
    st.subheader("📖 View Table Data")
    limit = st.number_input("Rows to load", min_value=1, max_value=10000, value=200, step=50)

    if st.button("📥 Load Data"):
        try:
            df, sql = fetch_table(host, user, passwd, database, table, int(limit))
            st.code(sql, language="sql")
            st.dataframe(df, use_container_width=True)
            st.session_state["last_df"] = df
        except Exception as e:
            st.error(f"Read failed: {e}")

    # -------------------------------
    # 4) Custom SELECT Query
    # -------------------------------
    with st.expander("🔎 Run Custom SELECT"):
        st.caption("Only SELECT queries allowed.")
        custom_sql = st.text_area("Write your SELECT query here", height=120)
        if st.button("▶️ Run Query"):
            try:
                df = run_select(host, user, passwd, database, custom_sql.strip())
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(f"Query failed: {e}")

    st.divider()

    # -------------------------------
    # 5) Add Row
    # -------------------------------
    st.subheader("➕ Add Row")

    cols_meta = get_table_columns(host, user, passwd, database, table)
    if not cols_meta:
        st.info("No column metadata found.")
    else:
        with st.form("add_row_form", clear_on_submit=True):
            st.caption("Fill values for columns (leave blank for auto-increment).")
            inputs = {}
            for col in cols_meta:
                name = col["name"]
                dtype = col["type"]
                extra = (col["extra"] or "").lower()

                if "auto_increment" in extra:
                    st.text_input(f"{name} ({dtype}) [auto]", value="", disabled=True)
                    continue

                val = st.text_input(f"{name} ({dtype})", value="")
                inputs[name] = None if val.strip() == "" else val

            submitted = st.form_submit_button("✅ Insert Row")
            if submitted:
                clean = {k: v for k, v in inputs.items() if v is not None}
                try:
                    affected, sql = insert_row(host, user, passwd, database, table, clean)
                    st.code(sql, language="sql")
                    st.success(f"Inserted {affected} row(s).")
                except Exception as e:
                    st.error(f"Insert failed: {e}")

    st.divider()

    # -------------------------------
    # 6) Delete
    # -------------------------------
    st.subheader("🗑️ Delete Row(s)")

    with st.form("delete_form"):
        where_clause = st.text_input("WHERE condition", placeholder="id = 1")
        delete_ok = st.form_submit_button("⚠️ Delete")
        if delete_ok:
            try:
                affected, sql = delete_rows(host, user, passwd, database, table, where_clause)
                st.code(sql, language="sql")
                st.success(f"Deleted {affected} row(s).")
            except Exception as e:
                st.error(f"Delete failed: {e}")

    st.divider()

    # -------------------------------
    # 7) Update
    # -------------------------------
    st.subheader("📝 Update Rows")

    with st.form("update_form"):
        set_part = st.text_input("SET clause", placeholder="col1='newvalue', col2=123")
        where_part = st.text_input("WHERE clause", placeholder="id = 1")
        upd = st.form_submit_button("✏️ Run Update")
        if upd:
            try:
                affected, sql = execute_update(host, user, passwd, database, table, set_part, where_part)
                st.code(sql, language="sql")
                st.success(f"Updated {affected} row(s).")
            except Exception as e:
                st.error(f"Update failed: {e}")
