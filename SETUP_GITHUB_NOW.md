# 🚀 Setup GitHub Repository - Bước Từng Bước

## 📋 Bước 1: Tạo Repository trên GitHub

### 1.1 Truy cập GitHub
- Mở trình duyệt và truy cập: [github.com](https://github.com)
- Đăng nhập vào tài khoản GitHub của bạn

### 1.2 Tạo Repository Mới
1. **Click nút "New"** (màu xanh lá) hoặc **"+"** → **"New repository"**
2. **Điền thông tin**:
   - **Repository name**: `lawyer-crawling-system`
   - **Description**: `Django-based lawyer data crawling system with Docker support`
   - **Visibility**: Chọn **Public** hoặc **Private**
   - **⚠️ QUAN TRỌNG**: **KHÔNG** check "Add a README file"
   - **⚠️ QUAN TRỌNG**: **KHÔNG** check "Add .gitignore"
   - **⚠️ QUAN TRỌNG**: **KHÔNG** check "Choose a license"
3. **Click "Create repository"**

### 1.3 Copy Repository URL
- Sau khi tạo xong, GitHub sẽ hiển thị URL
- **Copy URL** (sẽ có dạng: `https://github.com/username/lawyer-crawling-system.git`)

## 🔧 Bước 2: Thêm Remote Origin

### 2.1 Thêm Remote (Thay URL bằng repository của bạn)
```bash
# Thay "username" bằng tên GitHub của bạn
git remote add origin https://github.com/username/lawyer-crawling-system.git
```

### 2.2 Kiểm tra Remote
```bash
git remote -v
```

## 🚀 Bước 3: Đẩy Code lên GitHub

### 3.1 Đẩy Code
```bash
git push -u origin master
```

### 3.2 Nếu được hỏi Authentication
- **Username**: Tên GitHub của bạn
- **Password**: Sử dụng Personal Access Token (xem hướng dẫn bên dưới)

## 🔐 Bước 4: Tạo Personal Access Token (Nếu cần)

### 4.1 Tạo Token
1. **GitHub** → **Settings** (click avatar → Settings)
2. **Developer settings** (cuối trang bên trái)
3. **Personal access tokens** → **Tokens (classic)**
4. **Generate new token** → **Generate new token (classic)**
5. **Note**: `Lawyer Crawling System`
6. **Expiration**: `90 days` (hoặc tùy chọn)
7. **Scopes**: Check `repo` (Full control of private repositories)
8. **Generate token**
9. **Copy token** (chỉ hiển thị 1 lần)

### 4.2 Sử dụng Token
- Khi được hỏi password, **paste token** thay vì password GitHub

## ✅ Bước 5: Kiểm tra Kết quả

### 5.1 Truy cập Repository
- Mở repository trên GitHub
- Kiểm tra tất cả files đã được upload
- README.md sẽ hiển thị đẹp

### 5.2 Kiểm tra Local
```bash
git remote -v
git log --oneline
```

## 🆘 Troubleshooting

### Lỗi: "remote origin already exists"
```bash
git remote remove origin
git remote add origin https://github.com/username/lawyer-crawling-system.git
```

### Lỗi: "Authentication failed"
```bash
# Sử dụng token
git remote set-url origin https://username:token@github.com/username/repo.git
```

### Lỗi: "Repository not found"
- Kiểm tra URL repository
- Kiểm tra quyền truy cập
- Đảm bảo repository đã được tạo

## 📞 Cần Hỗ Trợ?

- **GitHub Help**: [help.github.com](https://help.github.com)
- **Git Documentation**: [git-scm.com/docs](https://git-scm.com)
- **Troubleshooting Guide**: Xem `TROUBLESHOOTING.md`

---

**Chúc bạn thành công! 🎉**
