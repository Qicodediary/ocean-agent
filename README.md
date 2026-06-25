# Ocean Box Model Agent — 两层海洋生物动力模型系统

## 更新说明

这个版本已经集成了**真实的两层海洋生物动力模型**，支持两个研究站点（BATS 和 HOT），可以根据不同的 GCM 模型和气候情景进行模拟。

---

## 数据文件夹结构

在启动系统之前，**必须**先准备好数据文件。文件夹结构如下：

```
project_root/
│
├── app/                           # 代码文件夹（已经有了）
├── worker.py                      # worker 脚本（已经有了）
│
└── data/                          # 新建：数据文件夹
    ├── BATS/
    │   ├── parameters/
    │   │   └── parameter_input_final.csv
    │   │
    │   ├── BCC-CSM2-MAR/
    │   │   ├── ssp585/
    │   │   │   ├── rsdscs_Omon_BCC-CSM2-MAR_ssp585_r1i1p1f1_1990-2100_BATS_daily.csv
    │   │   │   ├── rsds_Omon_BCC-CSM2-MAR_ssp585_r1i1p1f1_1990-2100_BATS_daily.csv
    │   │   │   └── mlotst_Omon_BCC-CSM2-MAR_ssp585_r1i1p1f1_1990-2100_BATS_daily.csv
    │   │   ├── ssp245/
    │   │   └── ssp126/
    │   │
    │   ├── CESM2-WACCM/
    │   │   ├── ssp585/
    │   │   └── ...
    │   │
    │   └── ... 其他3个BATS模型 ...
    │
    └── HOT/
        ├── parameters/
        │   └── parameter_input_final_HOT.csv
        │
        ├── CanESM5/
        │   ├── ssp585/
        │   │   ├── rsdscs_Omon_CanESM5_ssp585_r1i1p1f1_1990-2100_HOT_daily.csv
        │   │   ├── rsds_Omon_CanESM5_ssp585_r1i1p1f1_1990-2100_HOT_daily.csv
        │   │   └── mlotst_Omon_CanESM5_ssp585_r1i1p1f1_1990-2100_HOT_daily.csv
        │   └── ...
        │
        ├── CESM2-WACCM/
        │   └── ...
        │
        └── ... 其他8个HOT模型 ...
```

**关键点：**
- BATS 的参数文件是 `parameter_input_final.csv`，HOT 的是 `parameter_input_final_HOT.csv`
- BATS 的文件名包含 `gn` 字段，HOT 的不包含
- 每个模型的每个情景都需要三个变量文件：`rsdscs`、`rsds`、`mlotst`
- 文件名的格式**要完全匹配**上面的例子，代码会根据这个格式自动查找文件

---

## 第一步：准备数据

1. 在项目根目录新建 `data/` 文件夹
2. 根据上面的结构新建子文件夹
3. 把你的数据文件放进去（确保文件名格式正确）

---

## 第二步：启动系统（和之前一样）

开三个终端窗口，依次运行：

```bash
# 窗口1：Redis（如果还没启动）
redis-server

# 窗口2：Worker
source venv/bin/activate
python worker.py

# 窗口3：FastAPI
source venv/bin/activate
uvicorn app.main:app --reload
```

---

## 第三步：测试新的 API

打开浏览器访问 `http://127.0.0.1:8000/docs`

### 新的请求格式

现在 `POST /jobs` 的请求体包括 **station** 和 **model**：

```json
{
  "station": "BATS",
  "model": "BCC-CSM2-MAR",
  "scenario": "ssp585",
  "start_year": 2020,
  "end_year": 2050
}
```

**参数说明：**
- `station`: "BATS" 或 "HOT"
- `model`: 
  - BATS 可选：BCC-CSM2-MAR, CESM2-WACCM, CMCC-CM2-SR5, CMCC-ESM2, GFDL-ESM4
  - HOT 可选：CanESM5, CESM2-WACCM, CMCC-CM2-SR5, CMCC-ESM2, EC-Earth-Veg, EC-Earth3, GFDL-ESM4, IPSL-CM6A-LR, NorESM2-MM
- `scenario`: ssp126, ssp245, ssp585（具体可用情景取决于你的数据）
- `start_year`, `end_year`: 模拟的时间范围

### 测试流程

1. 在 `/docs` 页面找到 `POST /jobs`，点展开
2. 输入：
   ```json
   {
     "station": "BATS",
     "model": "BCC-CSM2-MAR",
     "scenario": "ssp585",
     "start_year": 2020,
     "end_year": 2025
   }
   ```
3. 点 Execute，会立刻收到 `job_id`
4. 模型会在后台跑，根据数据量可能要花几分钟到十几分钟
5. 用 `GET /jobs/{job_id}` 查询状态，跑完后会返回：
   - 各个生物地球化学变量的月均值统计
   - 生成的图表路径
   - 完整输出 CSV 文件路径

---

## 注意事项

- **def_solar_BATS.py**：你上传的模型核心函数文件需要放在项目根目录（和 worker.py 同级），这样才能被导入
- **数据完整性**：确保每个模型-情景组合都有 rsdscs、rsds、mlotst 三个文件，缺一不可
- **首次运行**：第一次运行某个模型可能会比较慢，之后会快一些（因为参数加载有开销）

---

## 排查问题

如果运行失败，检查：
1. Worker 窗口有没有报错？
2. 数据文件是否存在？路径和名称对不对？
3. 参数 CSV 文件有没有 'default' 列？

有问题把错误信息贴出来，我帮你看。


---

## 第一步：安装 Python 依赖

打开第一个终端，进入项目文件夹后运行：

```bash
# 建议先创建一个虚拟环境（避免和你电脑上其他项目的库冲突）
python3 -m venv venv
source venv/bin/activate    # Windows 用户改成: venv\Scripts\activate

# 安装所有需要的库
pip install -r requirements.txt
```

如果这一步出现红色报错，先把完整报错内容贴出来看看，不要自己瞎改。

---

## 第二步：安装并启动 Redis

Redis 不是 Python 库，是一个独立的小型数据库程序，需要单独安装。

**Mac 用户：**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Linux 用户：**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
```

**Windows 用户：**
推荐用 Docker（如果你还没装 Docker，先装 Docker Desktop），然后运行：
```bash
docker run -d -p 6379:6379 redis
```

**验证 Redis 是否正常运行：**
```bash
redis-cli ping
```
如果返回 `PONG`，说明 Redis 已经在跑了。这一步一定要先确认，
后面的步骤才有意义。

---

## 第三步：启动 Worker（厨师）

开第二个终端窗口，进入项目文件夹，激活虚拟环境后运行：

```bash
source venv/bin/activate   # 如果是新开的终端，要重新激活一次
python worker.py
```

看到类似这样的输出就说明成功了：
```
Worker 已启动，正在等待任务...
```

**这个窗口不要关**，让它一直开着。

---

## 第四步：启动 FastAPI 服务

开第三个终端窗口，进入项目文件夹，激活虚拟环境后运行：

```bash
source venv/bin/activate
uvicorn app.main:app --reload
```

看到类似这样的输出说明成功了：
```
Uvicorn running on http://127.0.0.1:8000
```

**这个窗口也不要关。**

---

## 第五步：测试整个系统

打开浏览器，访问：

```
http://127.0.0.1:8000/docs
```

你会看到一个自动生成的网页（这是 FastAPI 自带的功能，叫 Swagger UI），
上面列出了所有接口，可以直接在网页上点击测试，不需要写代码。

### 测试流程：

1. 找到 `POST /jobs` 这一项，点击展开，点 "Try it out"
2. 把请求体改成类似这样：
   ```json
   {
     "scenario": "SSP2-4.5",
     "start_year": 2020,
     "end_year": 2050,
     "variable": "SST"
   }
   ```
3. 点击 "Execute"，你会立刻拿到一个 `job_id`（比如 `"a1b2c3d4"`），
   注意：这一步是**立刻返回**的，不会卡住等待，因为任务已经丢给 worker 去做了
4. 切到跑 worker 的那个终端窗口，应该能看到类似：
   ```
   [job a1b2c3d4] 开始跑模型: SSP2-4.5, 2020-2050, 变量=SST
   ```
5. 等大约 10 秒后（因为假模型里设置的是 sleep 10秒），
   再去 `GET /jobs/{job_id}` 这一项，把刚才拿到的 job_id 填进去，点击 Execute
6. 一开始可能显示 `"status": "started"`，过几秒后再查一次，
   应该会变成 `"status": "finished"`，并且带上结果数据
7. 结果里的 `plot_path` 指向生成的图片，存在 `outputs/` 文件夹里，
   可以直接去文件夹里打开看

如果每一步都符合预期，说明整套异步系统已经跑通了。

---

## 下一步可以做什么

这个骨架跑通之后，接下来的工作大致是：

1. **把假模型换成真模型**：把 `app/box_model.py` 里 `run_box_model()`
   函数中间的部分，换成你真实调用 box model 的代码（输入CMIP6数据、
   跑模型、画图的逻辑），其他文件基本不用动。
2. **接入 CMIP6 数据**：在 `run_box_model()` 里加上根据 `scenario`
   参数自动去拉取对应 CMIP6 数据的逻辑。
3. **加上 AI Agent 层**：写一个能理解自然语言的 agent，让它自动
   把用户的话翻译成调用 `POST /jobs` 和 `GET /jobs/{job_id}` 的请求，
   不需要用户自己去填表单。这一步我们可以下一步再做。

---

## 常见问题排查

- **报错 "Connection refused" / 连不上 Redis**：说明 Redis 没启动，
  回去看第二步，先确认 `redis-cli ping` 能返回 `PONG`
- **POST /jobs 之后一直查不到 finished**：去看 worker 那个终端窗口
  有没有报错，如果 worker 窗口没动静，说明 worker 没收到任务，
  通常是 Redis 连接配置不对
- **`ModuleNotFoundError`**：说明虚拟环境没激活，或者 `pip install`
  那一步没装成功，回到第一步重新检查
