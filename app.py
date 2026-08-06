import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import koreanize_matplotlib

df = pd.read_csv("HR Data.csv")
#st.write(df)

def attrition_summary(data,group_column) :

    result = data.groupby(group_column,observed=True).agg(직원수=('퇴직','size'),퇴직자수 = ('퇴직','sum'), 퇴직률=('퇴직','mean')).reset_index()

    result['퇴직률'] = (result['퇴직률'] * 100).round(1)
    return result.sort_values('퇴직률', ascending=False)

total_employees=len(df)
#cols = st.columns(3)
df['퇴직'] = df['퇴직여부'].map({'No': 0, 'Yes': 1}).astype('int8')

total_attritions = df["퇴직"].sum()
overall_rate = round(df["퇴직"].mean() * 100, 1)
department_result = attrition_summary(df,'부서')

df['연령대'] = pd.cut(
    df['나이'],
    bins=[0, 29, 39, 49, 59, 100],
    labels=['20대 이하', '30대', '40대', '50대', '60대 이상']
)


age_result = attrition_summary(df,'연령대')

col1, col2, col3 = st.columns(3)

#with cols[0]:
col1.metric("전체 직원 수", f"{total_employees}명")
col2.metric("퇴직자 수", f"{total_attritions}명")
col3.metric("퇴직률", f"{overall_rate}%")

st.subheader("부서별 퇴직률")
fig1, ax1 = plt.subplots(figsize=(8, 4))
sns.barplot(department_result, x="퇴직률", y="부서", ax=ax1)
ax1.set_xlabel("퇴직률(%)")
st.pyplot(fig1)

st.subheader("연령대별 퇴직률")
fig2, ax2 = plt.subplots(figsize=(8, 4))
sns.barplot(age_result, x="연령대", y="퇴직률", ax=ax2)
ax2.set_xlabel("퇴직률(%)")
st.pyplot(fig2)