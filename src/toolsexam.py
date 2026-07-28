"""
tools.py
--------
Khai báo các Tool (công cụ) cho ReAct Agent "Gift Genie".
Toàn bộ dữ liệu là MOCK DATA (không gọi API thật) để tập trung vào
logic ReAct (Thought -> Action -> Observation) thay vì hạ tầng API.

5 tool chính:
  1. phan_tich_tinh_cach   -> suy ra nhóm tính cách từ mô tả người dùng
  2. tim_kiem_qua_tang     -> lọc catalog quà theo nhóm tính cách / sở thích / ngân sách
  3. tra_cuu_quy_tac_dip   -> tra các lưu ý / điều kiêng kỵ theo dịp lễ & văn hóa
  4. kiem_tra_ton_kho      -> kiểm tra 1 sản phẩm còn hàng hay không
  5. tinh_ngan_sach_gop    -> chia đều ngân sách khi nhiều người góp quà
"""

from typing import Optional


# ============================================================
# 1. MOCK DATA
# ============================================================

# --- Catalog quà tặng (15 sản phẩm, đa dạng nhóm tính cách & mức giá) ---
CATALOG_QUA_TANG = [
    {"ma_sp": "QT001", "ten": "Bộ màu vẽ nước cao cấp", "gia": 280000,
     "nhom_tinh_cach": ["sang_tao", "noi_tam"], "so_thich": ["vẽ", "nghệ thuật"], "ton_kho": 12},
    {"ma_sp": "QT002", "ten": "Sổ tay da handmade", "gia": 150000,
     "nhom_tinh_cach": ["noi_tam", "sang_tao"], "so_thich": ["viết lách", "đọc sách"], "ton_kho": 20},
    {"ma_sp": "QT003", "ten": "Sách best-seller (combo 2 cuốn)", "gia": 220000,
     "nhom_tinh_cach": ["noi_tam", "thuc_te"], "so_thich": ["đọc sách"], "ton_kho": 30},
    {"ma_sp": "QT004", "ten": "Tai nghe Bluetooth mini", "gia": 450000,
     "nhom_tinh_cach": ["cong_nghe", "huong_ngoai"], "so_thich": ["công nghệ", "âm nhạc"], "ton_kho": 8},
    {"ma_sp": "QT005", "ten": "Cây mini để bàn (bonsai giả)", "gia": 120000,
     "nhom_tinh_cach": ["thien_nhien", "noi_tam"], "so_thich": ["làm vườn", "cây cảnh"], "ton_kho": 25},
    {"ma_sp": "QT006", "ten": "Bộ dụng cụ làm vườn mini", "gia": 320000,
     "nhom_tinh_cach": ["thien_nhien", "thuc_te"], "so_thich": ["làm vườn"], "ton_kho": 10},
    {"ma_sp": "QT007", "ten": "Loa Bluetooth di động", "gia": 590000,
     "nhom_tinh_cach": ["cong_nghe", "huong_ngoai"], "so_thich": ["âm nhạc", "công nghệ"], "ton_kho": 6},
    {"ma_sp": "QT008", "ten": "Bộ trà thảo mộc cao cấp", "gia": 380000,
     "nhom_tinh_cach": ["thuc_te", "noi_tam"], "so_thich": ["trà", "thư giãn"], "ton_kho": 15},
    {"ma_sp": "QT009", "ten": "Đồng hồ đeo tay cổ điển", "gia": 950000,
     "nhom_tinh_cach": ["thuc_te", "huong_ngoai"], "so_thich": ["thời trang"], "ton_kho": 4},
    {"ma_sp": "QT010", "ten": "Bút ký cao cấp khắc tên", "gia": 480000,
     "nhom_tinh_cach": ["thuc_te", "sang_tao"], "so_thich": ["viết lách", "văn phòng"], "ton_kho": 0},
    {"ma_sp": "QT011", "ten": "Voucher spa thư giãn", "gia": 500000,
     "nhom_tinh_cach": ["noi_tam", "thuc_te"], "so_thich": ["thư giãn"], "ton_kho": 18},
    {"ma_sp": "QT012", "ten": "Bảng vẽ điện tử mini", "gia": 890000,
     "nhom_tinh_cach": ["sang_tao", "cong_nghe"], "so_thich": ["vẽ", "công nghệ"], "ton_kho": 7},
    {"ma_sp": "QT013", "ten": "Bình giữ nhiệt cá nhân hóa", "gia": 180000,
     "nhom_tinh_cach": ["thuc_te", "huong_ngoai"], "so_thich": ["thể thao", "du lịch"], "ton_kho": 22},
    {"ma_sp": "QT014", "ten": "Set nến thơm thiên nhiên", "gia": 210000,
     "nhom_tinh_cach": ["thien_nhien", "noi_tam"], "so_thich": ["thư giãn", "trang trí"], "ton_kho": 14},
    {"ma_sp": "QT015", "ten": "Combo văn phòng phẩm cao cấp", "gia": 260000,
     "nhom_tinh_cach": ["thuc_te", "sang_tao"], "so_thich": ["văn phòng", "viết lách"], "ton_kho": 19},
]

# --- Từ khóa để suy ra nhóm tính cách (rule-based, xác định - không "đoán mò") ---
TU_KHOA_TINH_CACH = {
    "sang_tao": ["sáng tạo", "vẽ", "nghệ thuật", "viết lách", "âm nhạc sáng tác", "thiết kế"],
    "noi_tam": ["nội tâm", "trầm tính", "ít nói", "hướng nội", "thích yên tĩnh", "ít thích chỗ đông người"],
    "huong_ngoai": ["hướng ngoại", "năng động", "thích tiệc tùng", "quảng giao", "sôi nổi"],
    "thuc_te": ["thực tế", "thực dụng", "tiết kiệm", "logic", "kỹ tính"],
    "cong_nghe": ["công nghệ", "gadget", "điện tử", "mê công nghệ", "yêu công nghệ"],
    "thien_nhien": ["thiên nhiên", "làm vườn", "cây cảnh", "yêu môi trường", "ngoài trời"],
}

# --- Quy tắc / điều kiêng kỵ theo dịp lễ & văn hóa ---
QUY_TAC_DIP_LE = {
    ("tết", "nhật bản"): {
        "nen_tranh": ["đồng hồ", "vật sắc nhọn (dao, kéo)", "số lượng 4 hoặc 9"],
        "nen_uu_tien": ["trà", "văn phòng phẩm cao cấp", "đồ trang trí tinh tế"],
        "ghi_chu": "Người Nhật coi đồng hồ tượng trưng cho thời gian cạn dần, tránh tặng cho người lớn tuổi/cấp trên."
    },
    ("tết", "việt nam"): {
        "nen_tranh": ["vật sắc nhọn", "đồ màu đen/trắng toàn bộ"],
        "nen_uu_tien": ["trà", "bánh mứt cao cấp", "quà mang ý nghĩa may mắn"],
        "ghi_chu": "Tránh tặng số lượng lẻ mang ý nghĩa xui rủi tùy vùng miền."
    },
    ("sinh nhật", None): {
        "nen_tranh": [],
        "nen_uu_tien": ["quà cá nhân hóa theo sở thích"],
        "ghi_chu": "Không có kiêng kỵ đặc biệt, ưu tiên cá nhân hóa theo tính cách người nhận."
    },
    ("valentine", None): {
        "nen_tranh": ["quà mang tính công việc/văn phòng thuần túy"],
        "nen_uu_tien": ["quà mang ý nghĩa tình cảm, lãng mạn"],
        "ghi_chu": "Ưu tiên yếu tố cảm xúc hơn giá trị vật chất."
    },
}


# ============================================================
# 2. TOOL FUNCTIONS
# ============================================================

def phan_tich_tinh_cach(mo_ta: str) -> dict:
    """
    Suy ra (các) nhóm tính cách từ đoạn mô tả tự do của người dùng,
    dựa trên khớp từ khóa xác định (rule-based) thay vì để LLM tự đoán.

    Args:
        mo_ta: đoạn văn mô tả tính cách/sở thích người nhận quà.

    Returns:
        dict: {"nhom_tinh_cach": [...], "tu_khoa_khop": {...}}
    """
    mo_ta_lower = mo_ta.lower()
    nhom_phat_hien = []
    tu_khoa_khop = {}

    for nhom, tu_khoas in TU_KHOA_TINH_CACH.items():
        khop = [tk for tk in tu_khoas if tk in mo_ta_lower]
        if khop:
            nhom_phat_hien.append(nhom)
            tu_khoa_khop[nhom] = khop

    if not nhom_phat_hien:
        return {
            "nhom_tinh_cach": [],
            "tu_khoa_khop": {},
            "canh_bao": "Không đủ dữ liệu để xác định nhóm tính cách. Cần thêm mô tả cụ thể hơn."
        }

    return {"nhom_tinh_cach": nhom_phat_hien, "tu_khoa_khop": tu_khoa_khop}


def tim_kiem_qua_tang(
    nhom_tinh_cach: Optional[str] = None,
    so_thich: Optional[str] = None,
    ngan_sach_min: int = 0,
    ngan_sach_max: int = 10_000_000,
    loai_tru: Optional[list] = None,
) -> dict:
    """
    Lọc catalog quà tặng theo nhóm tính cách, sở thích và khoảng ngân sách.

    Args:
        nhom_tinh_cach: một trong các key của TU_KHOA_TINH_CACH (vd 'sang_tao'). Có thể để None.
        so_thich: từ khóa sở thích tự do (vd 'đọc sách'). Có thể để None.
        ngan_sach_min, ngan_sach_max: khoảng giá (VND).
        loai_tru: danh sách từ khóa tên sản phẩm cần loại trừ (dùng khi có quy tắc kiêng kỵ).

    Returns:
        dict: {"ket_qua": [...], "so_luong": int}
    """
    loai_tru = loai_tru or []
    ket_qua = []

    for sp in CATALOG_QUA_TANG:
        if not (ngan_sach_min <= sp["gia"] <= ngan_sach_max):
            continue
        if nhom_tinh_cach and nhom_tinh_cach not in sp["nhom_tinh_cach"]:
            continue
        if so_thich and not any(so_thich.lower() in st.lower() for st in sp["so_thich"]):
            continue
        if any(tu.lower() in sp["ten"].lower() for tu in loai_tru):
            continue
        ket_qua.append(sp)

    return {"ket_qua": ket_qua, "so_luong": len(ket_qua)}


def tra_cuu_quy_tac_dip(dip_le: str, van_hoa: Optional[str] = None) -> dict:
    """
    Tra cứu các lưu ý / điều kiêng kỵ khi tặng quà theo dịp lễ và văn hóa.

    Args:
        dip_le: vd 'Tết', 'sinh nhật', 'Valentine'.
        van_hoa: vd 'Nhật Bản', 'Việt Nam'. Có thể để None nếu quy tắc chung.

    Returns:
        dict quy tắc, hoặc thông báo không tìm thấy.
    """
    key_chinh = dip_le.strip().lower()
    key_van_hoa = van_hoa.strip().lower() if van_hoa else None

    # Ưu tiên khớp đúng cả dịp lễ + văn hóa, sau đó fallback về dịp lễ chung
    for (d, v), quy_tac in QUY_TAC_DIP_LE.items():
        if d == key_chinh and v == key_van_hoa:
            return {"tim_thay": True, **quy_tac}

    for (d, v), quy_tac in QUY_TAC_DIP_LE.items():
        if d == key_chinh and v is None:
            return {"tim_thay": True, **quy_tac}

    return {
        "tim_thay": False,
        "ghi_chu": f"Chưa có dữ liệu quy tắc cho dịp '{dip_le}'"
                   + (f" / văn hóa '{van_hoa}'." if van_hoa else "."),
    }


def kiem_tra_ton_kho(ma_san_pham: str) -> dict:
    """
    Kiểm tra tình trạng tồn kho của một sản phẩm theo mã.

    Args:
        ma_san_pham: mã sản phẩm, vd 'QT001'.

    Returns:
        dict: {"ma_sp", "ten", "con_hang": bool, "so_luong": int}
    """
    for sp in CATALOG_QUA_TANG:
        if sp["ma_sp"] == ma_san_pham:
            return {
                "ma_sp": sp["ma_sp"],
                "ten": sp["ten"],
                "con_hang": sp["ton_kho"] > 0,
                "so_luong": sp["ton_kho"],
            }
    return {"loi": f"Không tìm thấy sản phẩm với mã '{ma_san_pham}'"}


def tinh_ngan_sach_gop(tong_tien: int, so_nguoi_gop: int) -> dict:
    """
    Chia đều ngân sách khi nhiều người cùng góp mua một món quà.

    Args:
        tong_tien: tổng ngân sách dự kiến (VND).
        so_nguoi_gop: số người tham gia góp quà.

    Returns:
        dict: {"moi_nguoi_gop": int, "tong_tien": int, "so_nguoi_gop": int}
    """
    if so_nguoi_gop <= 0:
        return {"loi": "Số người góp phải lớn hơn 0"}
    return {
        "tong_tien": tong_tien,
        "so_nguoi_gop": so_nguoi_gop,
        "moi_nguoi_gop": round(tong_tien / so_nguoi_gop),
    }


# ============================================================
# 3. TOOL SPECS (khai báo cho LLM function-calling / Anthropic tool use)
# ============================================================

TOOL_SPECS = [
    {
        "name": "phan_tich_tinh_cach",
        "description": (
            "Phân tích một đoạn mô tả tự do về người nhận quà (tính cách, thói quen, sở thích) "
            "và trả về (các) nhóm tính cách đã được xác định qua khớp từ khóa cố định. "
            "LUÔN gọi tool này TRƯỚC KHI gọi tim_kiem_qua_tang nếu người dùng mô tả tính cách "
            "bằng ngôn ngữ tự nhiên (chưa có nhóm tính cách rõ ràng)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "mo_ta": {
                    "type": "string",
                    "description": "Đoạn mô tả tính cách/sở thích của người nhận quà, bằng tiếng Việt tự nhiên."
                }
            },
            "required": ["mo_ta"],
        },
    },
    {
        "name": "tim_kiem_qua_tang",
        "description": (
            "Tìm kiếm trong catalog quà tặng theo nhóm tính cách, sở thích và khoảng ngân sách. "
            "Trả về danh sách rỗng nếu không có sản phẩm phù hợp — trong trường hợp đó KHÔNG được "
            "tự bịa sản phẩm, mà phải báo cho người dùng và đề xuất nới ngân sách hoặc tiêu chí."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "nhom_tinh_cach": {
                    "type": "string",
                    "description": "Một trong: sang_tao, noi_tam, huong_ngoai, thuc_te, cong_nghe, thien_nhien. Có thể bỏ trống."
                },
                "so_thich": {"type": "string", "description": "Từ khóa sở thích, vd 'đọc sách'. Có thể bỏ trống."},
                "ngan_sach_min": {"type": "integer", "description": "Ngân sách tối thiểu (VND)."},
                "ngan_sach_max": {"type": "integer", "description": "Ngân sách tối đa (VND)."},
                "loai_tru": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Danh sách từ khóa cần loại trừ khỏi kết quả (vd theo quy tắc kiêng kỵ)."
                },
            },
            "required": ["ngan_sach_min", "ngan_sach_max"],
        },
    },
    {
        "name": "tra_cuu_quy_tac_dip",
        "description": (
            "Tra cứu các điều nên tránh / nên ưu tiên khi tặng quà theo dịp lễ và văn hóa cụ thể. "
            "PHẢI gọi tool này trước tim_kiem_qua_tang mỗi khi người dùng đề cập một dịp lễ có yếu tố "
            "văn hóa/nghi thức (Tết, lễ truyền thống, đối tác nước ngoài...)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "dip_le": {"type": "string", "description": "Vd: 'Tết', 'sinh nhật', 'Valentine'."},
                "van_hoa": {"type": "string", "description": "Vd: 'Nhật Bản', 'Việt Nam'. Bỏ trống nếu không rõ."},
            },
            "required": ["dip_le"],
        },
    },
    {
        "name": "kiem_tra_ton_kho",
        "description": (
            "Kiểm tra một sản phẩm cụ thể (theo mã sản phẩm) còn hàng hay không trước khi chốt gợi ý "
            "cho người dùng. PHẢI gọi tool này cho sản phẩm được chọn cuối cùng trước khi trả lời."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ma_san_pham": {"type": "string", "description": "Mã sản phẩm, vd 'QT001'."}
            },
            "required": ["ma_san_pham"],
        },
    },
    {
        "name": "tinh_ngan_sach_gop",
        "description": "Chia đều một khoản ngân sách cho nhiều người cùng góp mua quà.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tong_tien": {"type": "integer", "description": "Tổng ngân sách dự kiến (VND)."},
                "so_nguoi_gop": {"type": "integer", "description": "Số người tham gia góp quà."},
            },
            "required": ["tong_tien", "so_nguoi_gop"],
        },
    },
]


# ============================================================
# 4. QUICK SELF-TEST (chạy: python src/tools.py)
# ============================================================

if __name__ == "__main__":
    print("== Test phan_tich_tinh_cach ==")
    print(phan_tich_tinh_cach("Bạn ấy thích vẽ, sống khá nội tâm, ít thích chỗ đông người"))

    print("\n== Test tim_kiem_qua_tang ==")
    print(tim_kiem_qua_tang(nhom_tinh_cach="sang_tao", ngan_sach_min=100000, ngan_sach_max=500000))

    print("\n== Test tra_cuu_quy_tac_dip (Tết - Nhật Bản) ==")
    print(tra_cuu_quy_tac_dip("Tết", "Nhật Bản"))

    print("\n== Test kiem_tra_ton_kho ==")
    print(kiem_tra_ton_kho("QT010"))  # sản phẩm hết hàng

    print("\n== Test tinh_ngan_sach_gop ==")
    print(tinh_ngan_sach_gop(900000, 4))

    print("\n== Test edge case: ngân sách quá thấp ==")
    print(tim_kiem_qua_tang(ngan_sach_min=0, ngan_sach_max=10000))
