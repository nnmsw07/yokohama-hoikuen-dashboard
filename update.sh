#!/bin/bash

set -e

echo "====================================="
echo "🛠 add period annotation"
echo "====================================="

python << 'EOF'
from pathlib import Path

path = Path("app.py")

text = path.read_text(
    encoding="utf-8"
)

anchor = '''
st.subheader("🟢 比較的入りやすい園")
'''

insert = '''
st.subheader("🟢 比較的入りやすい園")

st.caption(
    "※ 令和6年度〜令和8年度の月次データ平均をもとに算出"
)
'''

text = text.replace(
    anchor,
    insert
)

path.write_text(
    text,
    encoding="utf-8"
)

print("✅ annotation added")

EOF

echo ""
echo "====================================="
echo "✅ done"
echo "====================================="

echo ""
echo "RUN:"
echo "streamlit run app.py"
