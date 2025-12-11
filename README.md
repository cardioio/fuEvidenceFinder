# Python项目环境设置

## 虚拟环境

已为此项目创建了Python虚拟环境（venv）。

### 激活虚拟环境

在macOS/Linux上：
```bash
source venv/bin/activate
```

在Windows上：
```bash
venv\Scripts\activate
```

### 安装依赖

激活虚拟环境后，可以使用pip安装项目依赖：
```bash
pip install -r requirements.txt
```

### 退出虚拟环境

当完成工作时，可以退出虚拟环境：
```bash
deactivate
```

## 项目结构

```
fuEvidenceExcel/
├── venv/              # 虚拟环境
├── README.md          # 此文件
└── (其他项目文件)
```

## 注意事项

- 虚拟环境将项目依赖与系统Python环境隔离
- 每次开发前都需要激活虚拟环境
- 可以使用 `pip freeze > requirements.txt` 生成依赖列表