-- 更新管理员 admin 的密码为 Nemo@2018
UPDATE `admins` SET `password_hash` = '$2b$12$.IyxJaSimd0T4u12Zhezme8AX4IZmJMLVsXV0oiDNq0CetdJpHgGe' WHERE `username` = 'admin';