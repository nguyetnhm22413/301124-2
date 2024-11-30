import pandas as pd
import requests
from io import StringIO
import streamlit as st
import seaborn as sns

# URL của Google Sheets
sheet_id = '1A2EE7TrZrjULJkwHqdDXzoY5KOQkWAkcPxYxsC4B6rQ'
sheet_name = 'LogisticDataset'
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

# Đọc dữ liệu từ Google Sheets
@st.cache
def load_data():
    return pd.read_csv(url)

# Hàm làm sạch dữ liệu
def clean_data(df):
    # Loại bỏ các cột không cần thiết
    df = df.T.drop_duplicates(keep='first').T
    df = df.drop(columns=['Customer Email', 'Product Description', 'Order Zipcode', 'Customer Zipcode',
                          'Product Image', 'Latitude', 'Longitude', 'Customer Fname', 'Customer Lname',
                          'Product Status', 'Category Id', 'Department Id', 'Customer Id', 'Order Id',
                          'Order Item Cardprod Id'])

    # Xác định các nhóm cột
    category_cols = ['Type', 'Delivery Status', 'Late_delivery_risk', 'Category Name', 'Customer Country',
                     'Customer City', 'Customer State','Customer Street', 'Customer Segment', 'Department Name',
                     'Order City', 'Order Country', 'Order Region', 'Order State', 'Order Status', 'Product Name',
                     'Shipping Mode','Market']

    float_cols = ['Order Item Id', 'Order Item Quantity', 'Days for shipping (real)', 'Days for shipment (scheduled)',
                  'Benefit per order', 'Sales per customer', 'Order Item Discount', 'Order Item Discount Rate',
                  'Order Item Product Price', 'Order Item Profit Ratio', 'Sales']

    datetime_cols = ['order date (DateOrders)', 'shipping date (DateOrders)']

    # Chuyển đổi kiểu dữ liệu
    df[category_cols] = df[category_cols].astype('category')
    df[float_cols] = df[float_cols].apply(pd.to_numeric, downcast='float', errors='coerce')
    df[datetime_cols] = df[datetime_cols].apply(pd.to_datetime, errors='coerce')

    # Xử lý giá trị null
    for column in df.columns:
        if df[column].isnull().any():
            if df[column].dtype == 'float':
                df[column].fillna(df[column].mean(), inplace=True)
            else:
                df[column].fillna(df[column].mode()[0], inplace=True)

    # Làm sạch tên cột
    df.columns = [col.lower().replace(' ', '_') for col in df.columns]
    df.rename(columns=lambda x: x.replace("(", "").replace(")", ""), inplace=True)

    # Loại bỏ ký tự '?'
    for i in df.columns:
        if df[i].dtype.name == 'category':
            df[i] = df[i].cat.add_categories([val.replace('?', '') for val in df[i].unique() if '?' in str(val)])
        for j in range(len(df[i])):
            value = str(df[i][j])
            if '?' in value:
                df.at[j, i] = value.replace('?', '')
    return df

# Streamlit App
st.title("Data Cleaning App with Streamlit")

# Tải file dữ liệu
uploaded_file = st.file_uploader("Tải lên tệp dữ liệu CSV", type=["csv"])
if uploaded_file:
    # Đọc dữ liệu
    df = pd.read_csv(uploaded_file)
    st.write("### Dữ liệu ban đầu:")
    st.dataframe(df.head())

    # Làm sạch dữ liệu
    cleaned_df = clean_data(df)
    st.write("### Dữ liệu sau khi làm sạch:")
    st.dataframe(cleaned_df.head())

    # Hiển thị thông tin dữ liệu
    st.write("### Thông tin dữ liệu:")
    buffer = StringIO()
    cleaned_df.info(buf=buffer)
    st.text(buffer.getvalue())

import matplotlib.pyplot as plt
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import LabelEncoder, RobustScaler

# Hàm tìm ranh giới Boxplot
def find_boxplot_boundaries(col: pd.Series, whisker_coeff: float = 1.5):
    Q1 = col.quantile(0.25)
    Q3 = col.quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - whisker_coeff * IQR
    upper = Q3 + whisker_coeff * IQR
    return lower, upper

# Class cắt giá trị outlier
class BoxplotOutlierClipper(BaseEstimator, TransformerMixin):
    def __init__(self, whisker_coeff: float = 1.5):
        self.whisker = whisker_coeff
        self.lower = None
        self.upper = None

    def fit(self, X: pd.Series):
        self.lower, self.upper = find_boxplot_boundaries(X, self.whisker)
        return self

    def transform(self, X):
        return X.clip(self.lower, self.upper)

# Xử lý kiểu dữ liệu
st.write("### Xử lý kiểu dữ liệu:")
category_cols = [
        "Type",
        "Delivery Status",
        "Late_delivery_risk",
        "Category Name",
        "Customer Country",
        "Customer City",
        "Customer State",
        "Customer Street",
        "Customer Segment",
        "Department Name",
        "Order City",
        "Order Country",
        "Order Region",
        "Order State",
        "Order Status",
        "Product Name",
        "Shipping Mode",
        "Market",
    ]
float_cols = [
        "Order Item Id",
        "Order Item Quantity",
        "Days for shipping (real)",
        "Days for shipment (scheduled)",
        "Benefit per order",
        "Sales per customer",
        "Order Item Discount",
        "Order Item Discount Rate",
        "Order Item Product Price",
        "Order Item Profit Ratio",
        "Sales",
    ]


# Chuẩn hóa dữ liệu
st.write("### Chuẩn hóa dữ liệu:")
robust_scaler = RobustScaler()
scaled_cols = [
        "Benefit per order",
        "Sales per customer",
        "Order Item Discount",
        "Order Item Discount Rate",
        "Order Item Product Price",
        "Order Item Profit Ratio",
        "Sales",
    ]
df[scaled_cols] = robust_scaler.fit_transform(df[scaled_cols])
st.dataframe(df[scaled_cols].head())

# Trực quan hóa
st.write("### Trực quan hóa dữ liệu:")
fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(15, 5))
df[["Days for shipping (real)"]].hist(bins=50, ax=axes[0])
axes[0].set_title("Histogram - Days for Shipping (Real)")
df[["Days for shipping (real)"]].boxplot(ax=axes[1], vert=False)
axes[1].set_title("Boxplot - Days for Shipping (Real)")
st.pyplot(fig)

# Tạo cột mới "Late Days"
st.write("### Tạo cột 'Late Days':")
df["Late Days"] = df["Days for shipping (real)"] - df["Days for shipment (scheduled)"]
st.dataframe(df[["Late Days"]].head())


# Market Distribution Pie Chart
st.write("### Market Distribution")
fig, ax = plt.subplots()
df['market'].value_counts().plot.pie(autopct='%1.1f%%', startangle=90, colors=sns.color_palette('pastel'), ax=ax)
ax.set_title('Market Distribution')
ax.set_ylabel('')
st.pyplot(fig)

# Customer Segment Distribution Pie Chart
st.write("### Customer Segment Distribution")
fig, ax = plt.subplots()
df['customer_segment'].value_counts().plot.pie(autopct='%1.1f%%', startangle=90, colors=sns.color_palette('pastel'), ax=ax)
ax.set_title('Customer Segment Distribution')
ax.set_ylabel('')
st.pyplot(fig)

# Category Name Count Bar Chart
st.write("### Count of Each Category Name")
category_counts = df['category_name'].value_counts()
fig, ax = plt.subplots(figsize=(12, 6))
sns.barplot(x=category_counts.index, y=category_counts.values, palette='coolwarm', ax=ax)
ax.set_title('Count of Each Category Name')
ax.set_xlabel('Category Name')
ax.set_ylabel('Count')
ax.tick_params(axis='x', rotation=45)
st.pyplot(fig)

# Top 10 Products Bar Chart
st.write("### Top 10 Most Common Products")
product_counts = df['product_name'].value_counts().nlargest(10)
fig, ax = plt.subplots(figsize=(12, 6))
sns.barplot(x=product_counts.index, y=product_counts.values, palette='coolwarm', ax=ax)
ax.set_title('Top 10 Most Common Products')
ax.set_xlabel('Product Name')
ax.set_ylabel('Count')
ax.tick_params(axis='x', rotation=45)
st.pyplot(fig)

# Pairplot of Continuous Variables
st.write("### Pair Plot of Continuous Variables")
fig = sns.pairplot(df[['sales_per_customer', 'benefit_per_order', 'order_item_product_price']], diag_kind='kde', palette='coolwarm')
st.pyplot(fig)

# Distribution Plots
st.write("### Distribution of Days for Shipping (Real)")
fig, ax = plt.subplots(figsize=(14, 6))
sns.histplot(df['days_for_shipping_real'], kde=True, color='blue', ax=ax)
ax.set_title('Distribution of Days for Shipping (Real)')
ax.set_xlabel('Days for Shipping (Real)')
ax.set_ylabel('Frequency')
st.pyplot(fig)

st.write("### Distribution of Days for Shipment (Scheduled)")
fig, ax = plt.subplots(figsize=(14, 6))
sns.histplot(df['days_for_shipment_scheduled'], kde=True, color='blue', ax=ax)
ax.set_title('Distribution of Days for Shipment (Scheduled)')
ax.set_xlabel('Days for Shipment (Scheduled)')
ax.set_ylabel('Frequency')
st.pyplot(fig)

# Correlation Heatmap
st.write("### Correlation Heatmap")
numeric_df = df.select_dtypes(include=['number'])
fig, ax = plt.subplots(figsize=(16, 14))
sns.heatmap(numeric_df.corr(), annot=True, cmap='coolwarm', vmin=-1, vmax=1, fmt=".2f", ax=ax, annot_kws={"size": 8})
ax.set_title('Correlation Heatmap')
st.pyplot(fig)

from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

# Ứng dụng Streamlit
st.title("Logistics Prediction App")

# Giả lập dữ liệu và mô hình (để thay thế bằng dữ liệu thực tế)
def create_sample_data():
    np.random.seed(0)
    data = {
        "days_for_shipping_real": np.random.randint(1, 10, 100),
        "days_for_shipment_scheduled": np.random.randint(1, 10, 100),
        "sales_per_customer": np.random.randint(100, 1000, 100),
        "benefit_per_order": np.random.randint(-100, 500, 100),
        "late_delivery_risk": np.random.choice([0, 1], 100),
        "sales": np.random.randint(1000, 10000, 100),
    }
    return pd.DataFrame(data)

# Load dữ liệu mẫu
df = create_sample_data()

# Tạo mô hình giả lập
clf = RandomForestClassifier()
reg = RandomForestRegressor()
clf.fit(df[["days_for_shipping_real", "days_for_shipment_scheduled", "sales_per_customer", "benefit_per_order"]], df["late_delivery_risk"])
reg.fit(df[["days_for_shipping_real", "days_for_shipment_scheduled", "sales_per_customer", "benefit_per_order"]], df["sales"])

# Lấy thông tin từ người dùng
st.sidebar.header("Nhập thông tin giao hàng và bán hàng")

days_for_shipping_real = st.sidebar.number_input("Days for Shipping (Real)", min_value=1, max_value=30, value=5)
days_for_shipment_scheduled = st.sidebar.number_input("Days for Shipment (Scheduled)", min_value=1, max_value=30, value=5)
sales_per_customer = st.sidebar.number_input("Sales per Customer", min_value=0, max_value=10000, value=500)
benefit_per_order = st.sidebar.number_input("Benefit per Order", min_value=-500, max_value=1000, value=100)

# Dự báo kết quả
user_input = np.array([[days_for_shipping_real, days_for_shipment_scheduled, sales_per_customer, benefit_per_order]])
delivery_risk = clf.predict(user_input)[0]
predicted_sales = reg.predict(user_input)[0]

# Hiển thị kết quả
st.write("### Kết quả dự đoán")
st.write(f"**Khả năng giao hàng trễ:** {'Có' if delivery_risk == 1 else 'Không'}")
st.write(f"**Dự báo doanh số (Sales):** ${predicted_sales:.2f}")
