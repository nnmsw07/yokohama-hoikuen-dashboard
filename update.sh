#!/bin/bash

set -e

echo "====================================="
echo "🛠 fix broken hensachi scale"
echo "====================================="

python << 'EOF'
from pathlib import Path

# =====================================
# model.py
# =====================================

model_path = Path("model.py")

text = model_path.read_text(
    encoding="utf-8"
)

# rank壁弱化

text = text.replace(

    'rank_score * 20',

    'rank_score * 10'

)

model_path.write_text(
    text,
    encoding="utf-8"
)

print("✅ model.py fixed")

# =====================================
# app.py
# =====================================

app_path = Path("app.py")

text = app_path.read_text(
    encoding="utf-8"
)

old = '''
user_hensachi = round(

    (
        (user_score - score_mean)
        / score_std
    ) * 10 + 50,

    1

)
'''

new = '''
user_hensachi = round(

    (
        (user_score - score_mean)
        / score_std
    ) * 10 + 50,

    1

)

# =================================
# clamp
# =================================

user_hensachi = float(

    np.clip(

        user_hensachi,

        20,
        80

    )

)
'''

text = text.replace(
    old,
    new
)

# threshold側もclamp

old = '''
threshold_hensachi = round(

    (
        (threshold - score_mean)
        / score_std
    ) * 10 + 50,

    1

)
'''

new = '''
threshold_hensachi = round(

    (
        (threshold - score_mean)
        / score_std
    ) * 10 + 50,

    1

)

threshold_hensachi = float(

    np.clip(

        threshold_hensachi,

        20,
        80

    )

)
'''

text = text.replace(
    old,
    new
)

app_path.write_text(
    text,
    encoding="utf-8"
)

print("✅ app.py fixed")

EOF

echo ""
echo "====================================="
echo "✅ done"
echo "====================================="

echo ""
echo "EXPECTED:"
echo "・偏差値100消える"
echo "・50前後中心になる"
echo "・横浜保活っぽい分布"
echo ""
echo "RUN:"
echo "pkill -f streamlit"
echo "streamlit run app.py"
