# 🚀 Quick GitHub Push Guide

## 📋 Bước 1: Tạo Repository trên GitHub

1. Truy cập [github.com](https://github.com) và đăng nhập
2. Click "New repository" (nút "+" màu xanh)
3. Điền thông tin:
   - **Repository name**: `lawyer-crawling-system`
   - **Description**: `Django lawyer data crawling system with Docker`
   - **Visibility**: Public hoặc Private
   - **KHÔNG** check "Add a README file"
4. Click "Create repository"
5. **Copy URL** của repository (sẽ cần cho bước sau)

## 🔧 Bước 2: Cấu hình Git (nếu chưa có)

```bash
# Cấu hình user (thay thế thông tin của bạn)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## 🚀 Bước 3: Đẩy Code lên GitHub

### Option A: Sử dụng Script Tự Động
```bash
# Chạy script (sẽ hướng dẫn từng bước)
./push_to_github.sh
```

### Option B: Thực hiện Thủ Công
```bash
# Thêm remote repository (thay URL bằng repository của bạn)
git remote add origin https://github.com/username/lawyer-crawling-system.git

# Đẩy code lên GitHub
git push -u origin master
```

## 🔐 Bước 4: Xác thực (Authentication)

Khi được hỏi username/password:
- **Username**: Tên GitHub của bạn
- **Password**: Sử dụng Personal Access Token (không phải password GitHub)

### Tạo Personal Access Token:
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token"
3. Chọn scope: `repo` (Full control of private repositories)
4. Copy token và sử dụng thay password

## ✅ Kiểm tra Kết quả

Sau khi push thành công:
1. Truy cập repository trên GitHub
2. Kiểm tra tất cả files đã được upload
3. README.md sẽ hiển thị đẹp với markdown

## 🆘 Nếu Gặp Lỗi

### Lỗi: "remote origin already exists"
```bash
git remote remove origin
git remote add origin https://github.com/username/lawyer-crawling-system.git
```

### Lỗi: "Authentication failed"
```bash
# Sử dụng token thay password
git remote set-url origin https://username:token@github.com/username/repo.git
```

### Lỗi: "Repository not found"
- Kiểm tra URL repository
- Kiểm tra quyền truy cập repository
- Đảm bảo repository đã được tạo

## 📞 Cần Hỗ Trợ?

- **GitHub Docs**: [docs.github.com](https://docs.github.com)
- **Git Tutorial**: [git-scm.com](https://git-scm.com)
- **Troubleshooting**: Xem `GITHUB_SETUP.md` để biết thêm chi tiết

---

**Chúc bạn thành công! 🎉**
