import streamlit as st
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go


def render_tab(orders_path, users_path, books_path, year_key, month_key):
    orders_df = pd.read_csv(orders_path)
    users_df = pd.read_csv(users_path)
    books_df = pd.read_csv(books_path)

    orders_df['date'] = pd.to_datetime(orders_df['date'])

    daily_revenue = orders_df.groupby('date')['paid_price'].sum().reset_index()
    daily_revenue.columns = ['date', 'revenue']

    top5 = daily_revenue.nlargest(5, 'revenue').copy()
    top5['date'] = top5['date'].dt.strftime('%Y-%m-%d')
    top5['rank'] = range(1, 6)

    top5_fig = go.Figure(data=[go.Table(
        columnwidth=[30, 150, 150],
        header=dict(values=['#', 'Date', 'Revenue $'], fill_color='#2c3e50', font=dict(color='white', size=14), align='center'),
        cells=dict(values=[top5['rank'], top5['date'], top5['revenue']], fill_color=[['#f9f9f9', '#ffffff'] * 3], font=dict(size=13), align='center', height=35)
    )])
    top5_fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=220)

    parent = {i: i for i in users_df.index}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        parent[find(x)] = find(y)

    def is_same_user(r1, r2):
        matches = (
            (r1['name'] == r2['name']) +
            (r1['address'] == r2['address']) +
            (r1['phone'] == r2['phone']) +
            (r1['email'] == r2['email'])
        )
        return matches >= 3

    records = users_df.reset_index().to_dict('records')
    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            if is_same_user(records[i], records[j]):
                union(records[i]['index'], records[j]['index'])

    unique_users = len(set(find(i) for i in users_df.index))
    unique_set_of_authors = books_df['author'].nunique()

    merged_books = orders_df.merge(books_df, left_on='book_id', right_on='id')
    author_sales = merged_books.groupby('author')['quantity'].sum().reset_index()
    author_sales.columns = ['author', 'total_sold']
    most_popular = author_sales.nlargest(1, 'total_sold')
    author_name = most_popular['author'].values[0]
    author_sold = most_popular['total_sold'].values[0]

    users_df['user_group'] = [find(i) for i in users_df.index]
    merged_users = orders_df.merge(users_df[['id', 'user_group']], left_on='user_id', right_on='id')
    spending = merged_users.groupby('user_group')['paid_price'].sum().reset_index()
    spending.columns = ['user_group', 'total_spent']
    top_group = spending.nlargest(1, 'total_spent')['user_group'].values[0]
    best_buyer_ids = users_df[users_df['user_group'] == top_group]['id'].tolist()
    total_spent = spending[spending['user_group'] == top_group]['total_spent'].values[0]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
            <div style="border:1px solid #2c3e50; border-radius:10px; padding:20px; text-align:center">
                <p style="color:gray; font-size:17px; margin:0">Unique Users</p>
                <p style="font-size:25px; font-weight:bold; margin:5px 0">{unique_users}</p>
                <hr style="border:0.5px solid #eeeeee">
                <p style="color:gray; font-size:17px; margin:0">Unique Set of Authors</p>
                <p style="font-size:25px; font-weight:bold; margin:5px 0">{unique_set_of_authors}</p>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div style="border:1px solid #2c3e50; border-radius:10px; padding:20px; text-align:center">
                <p style="color:gray; font-size:13px; margin:0">Best Buyer IDs</p>
                <p style="font-size:20px; font-weight:bold; margin:5px 0">{best_buyer_ids}</p>
                <hr style="border:0.5px solid #eeeeee">
                <p style="color:gray; font-size:13px; margin:0">Total Spent</p>
                <p style="font-size:20px; font-weight:bold; margin:5px 0">${total_spent:,.2f}</p>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
            <div style="border:1px solid #2c3e50; border-radius:10px; padding:20px; text-align:center">
                <p style="color:gray; font-size:13px; margin:0">Most Popular Author</p>
                <p style="font-size:20px; font-weight:bold; margin:5px 0">{author_name}</p>
                <hr style="border:0.5px solid #eeeeee">
                <p style="color:gray; font-size:13px; margin:0">Total Sold</p>
                <p style="font-size:20px; font-weight:bold; margin:5px 0">{author_sold} books</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("#### Top 5 days by revenue")
    st.plotly_chart(top5_fig, use_container_width=True)

    st.markdown("#### Daily Revenue")
    years = sorted(daily_revenue['date'].dt.year.unique())
    months = {1:'January', 2:'February', 3:'March', 4:'April', 5:'May', 6:'June',
              7:'July', 8:'August', 9:'September', 10:'October', 11:'November', 12:'December'}

    col_y, col_m = st.columns(2)
    with col_y:
        selected_year = st.selectbox('Year', ['All'] + years, key=year_key)
    with col_m:
        selected_month = st.selectbox('Month', ['All'] + list(months.values()), key=month_key)

    filtered = daily_revenue.copy()
    if selected_year != 'All':
        filtered = filtered[filtered['date'].dt.year == selected_year]
    if selected_month != 'All':
        month_num = list(months.values()).index(selected_month) + 1
        filtered = filtered[filtered['date'].dt.month == month_num]

    st.plotly_chart(px.line(filtered, x='date', y='revenue', title='Daily Revenue'), use_container_width=True)


st.set_page_config(page_title="Sales Dashboard", layout="wide")
st.markdown("<h1 style='text-align:center; color:#2c3e50'>📊 Sales Dashboard</h1>", unsafe_allow_html=True)
st.divider()

data1_tab, data2_tab, data3_tab = st.tabs(["DATA1", "DATA2", "DATA3"])

with data1_tab:
    render_tab('DATA1/data1/orders_clean.csv', 'DATA1/data1/users_clean.csv', 'DATA1/data1/books_clean.csv', 'year1', 'month1')

with data2_tab:
    render_tab('DATA2/data2/orders_clean.csv', 'DATA2/data2/users_clean.csv', 'DATA2/data2/books_clean.csv', 'year2', 'month2')

with data3_tab:
    render_tab('DATA3/data3/orders_clean.csv', 'DATA3/data3/users_clean.csv', 'DATA3/data3/books_clean.csv', 'year3', 'month3')