# AWS Lightsail + Clash：AI 执行手册

从选服务器、核实赠金，到部署 VLESS/REALITY、国内外分流、Google Play 下载、HTTPS 订阅、月流量显示、Claude 固定出口及 DNS 加固。默认使用 **Lightsail 新加坡、Ubuntu 24.04 LTS、Xray + Mihomo、Caddy**。

本文件包含完整配置和脚本，单独下载 README 即可交给有浏览器、终端和文件操作能力的 AI 执行。账号登录、付款信息、验证码和授权由账号所有者完成；其余步骤连续执行。**“一键”指一次下达任务后由 AI 推进，不代表跳过云资源费用和权限确认。**

更新日期：2026-10-27。基础链路来自实际部署；以下模板已脱敏。价格、赠金活动、客户端版本应在执行当天复核。新账号、新服务器仍须完成本文验收，不能把既有案例当成本次成功证据。

## 1. 复制这段话给 AI

```text
请完整阅读这份 README，并按顺序实施。

目标：部署个人使用的 AWS Lightsail 新加坡节点，让 Mac 和 Android
通过同一条 HTTPS 订阅使用；国内和局域网直连、国外走节点；
Google Play 可下载；Clash 显示本月服务器 NetworkIn + NetworkOut / 套餐额度；
Claude 官方请求与 DNS 固定经 AWS；Mac 阻止物理网卡直接发出 53/853 流量。

默认：Ubuntu 24.04 LTS x86_64、含公网 IPv4 的 1GB Lightsail 套餐，
基准价 7 美元/月、2TB/月；先确认执行当天价格与账号赠金覆盖范围。
复用我已有的登录态、服务器和客户端；发现已有部署先检查，禁止重复购买、
重置凭据、覆盖其他订阅或删除既有资源。

请先只读检查并列出简短执行链路。常规细节直接按本文选择，不反复问选型。
创建付费资源、升级账号限制、开放公网端口、接受证书协议、
新建长期 IAM 凭据或安装 Mac PF 防护前，准备好具体变更与回退方法，
再按工具要求请求确认。
密码、验证码、付款资料和 MFA 操作交给我本人完成。

执行各阶段后记录实际证据，失败先定位并尝试合理替代路径。
CloudShell 不可用时用 Lightsail 浏览器 SSH，不为此开放 0.0.0.0/0 的 22 端口。
所有密钥和真实订阅 URL 仅保存到本机或本人的服务器私密文件，不上传公共仓库。
完成后交付订阅链接、脱敏验收结果、维护方法和确实未完成的设备验证。
关闭你创建且已不再使用的浏览器标签，保留我手工打开的页面。
```

## 2. 参数、状态与完成标准

AI 先读取现有环境，再填写下表；只有账号归属、费用上限、目标设备等核心信息缺失时才提问。

| 参数 | 默认或来源 |
|---|---|
| `REGION` | `ap-southeast-1`，新加坡 |
| `INSTANCE_NAME` | `personal-proxy-sg`；已有实例则使用实际名称 |
| `SERVER_IPV4` | 实例绑定的静态公网 IPv4，不能填动态地址或示例地址 |
| `SNI` | `www.amazon.com`；必须先从服务器验证目标 TLS 能力 |
| `QUOTA_BYTES` | `2199023255552`，本模板按 2 × 1024⁴ 显示 2TB；套餐不同时修改 |
| `NODE_NAME` | `AWS 新加坡` |
| `SSH_PATH` | Lightsail 浏览器 SSH，或已经授权且限制来源的 SSH |
| `LOCAL_CLIENT` | Mac：Clash Verge Rev；Android：维护中的 Mihomo 客户端 |

在仓库之外建立私密工作目录，权限 `0700`，保存 `state.json`：阶段、资源名称、当前版本、已获授权、检查结果和文件路径。不要把真实密钥写进状态摘要。保存每个被修改文件的旧副本，只恢复本次修改的文件。

完成标准：

1. 实例、静态 IPv4、套餐费用、赠金适用范围均有实际页面或 API 证据。
2. Xray、订阅服务和流量定时器启用；Google、YouTube、UDP 测试通过。
3. 国内业务请求匹配 `DIRECT`；国外请求和 Google Play 入口匹配代理；Claude 官方请求及 DNS 固定 AWS。
4. HTTPS 订阅通过正常证书校验，错误路径返回 404，下载内容与服务器源文件一致。
5. Mac 用远程订阅显示月流量；手机端逐项标注“已实测”或“待用户验证”。
6. Mac TUN 的 UDP/TCP DNS 均可用，物理网卡 53/853 出站被拦截；切订阅和重启后复验。

## 3. 选服务器、获取并核实赠金

### 3.1 固定选型

个人代理先选 Lightsail，使用包含流量额度的套餐。本流程不需要 EC2、负载均衡器、NAT Gateway、托管数据库或付费控制面板。

2026-10-26 的 Linux/Unix、含公网 IPv4 通用套餐：**2 vCPU、1GB RAM、40GB SSD、2TB/月，7 美元/月**。创建时以新加坡控制台实际显示为准，价格变化或超出预算先确认。[官方价格](https://aws.amazon.com/lightsail/pricing/)

这里的 7 美元是资源月度标价，不是账号会员费；Lightsail 按小时累计至月度上限。停机仍会计费，删除实例才停止该实例费用；删除不属于本流程自动操作。[账单说明](https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-frequently-asked-questions-faq-billing-and-account-management.html)

### 3.2 赠金操作顺序

1. 使用已有 AWS 登录态。新账号由用户填写身份、付款资料、密码和验证码；AI 不读取或保存这些内容。
2. 打开当前账号的 Free Tier／Explore AWS 活动页，记录实际可获得的任务、金额、限制和截止日期。官方新客页面目前说明初始 100 美元、完成任务再获最高 100 美元；不是每个已有账号都有资格。[官方 Free Tier](https://aws.amazon.com/free/)
3. **先查看可领取任务，再升级账号能力。** 如果页面有“使用 AWS Budgets 设置成本预算”奖励，按任务入口创建适合当前套餐的预算，完成后刷新活动页与 Credits 页核实到账。没有任务就跳过，不能编造奖励。
4. 预算只设成本提醒，阈值使用用户确认的月度上限；不要开启自动停止或删除资源的预算动作。若有邮箱通知，确认收件人后配置。
5. 在 Billing → Credits 逐条确认 `Active`、剩余额度、到期日期和 Applicable products；必须看到 **Amazon Lightsail**。本案例曾实际确认 100 + 20 美元，不能把 120 美元写成人人可领的固定结果。
6. 若创建资源的项目账号与拥有赠金的账号不同，检查组织账单的 Credit sharing 是否覆盖实际资源账号。无需复制账号 ID 到公开文档。
7. 创建资源后核对 Bills、Credits 应用记录和 Payments。新建资源的账单存在延迟；“暂时 0 美元”不能证明不计费。赠金耗尽、过期或不适用的费用仍可能收费。[赠金抵扣与组织共享](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/useconsolidatedbilling-credits.html)

### 3.3 新版账号的地区限制分支

普通完整 AWS 账号能进入新加坡 Lightsail，就跳过本节。若 Builder ID／项目式控制台只显示固定区域：

1. 先确认是可见区域设置、项目能力限制，还是组织 SCP 的显式拒绝，记录实际报错。
2. 在账号实际显示的活动页完成仍可领取且用户授权的任务，再查看 Advanced／完整控制台的升级说明。若页面提示失去后续奖励资格、移除费用上限或升级不可逆，向用户说明具体变化并等待确认。
3. 如果错误明确来自已有区域策略，例如 `RegionFloor`，只把 `ap-southeast-1` 加到原有允许区域列表。保留其他条件、全局服务例外和整个策略的其余内容。不要删除 SCP、替换成 AllowAll，或为消除校验提示删除无关 action。
4. 如果还存在 `ConsoleVisibleRegions` 设置，单独使新加坡可见；“能在下拉框看到区域”和“有权限创建实例”分别验证。

这部分依据账号实际 UI 执行，不存在适用于所有 AWS 账号的固定“一条开通命令”。

## 4. 创建实例与网络

创建前展示：区域、Linux 套餐、月费、额度、赠金证据和拟开放端口。获得对应授权后执行。

1. Lightsail → Create instance：新加坡、Linux/Unix、**OS Only → Ubuntu 24.04 LTS**、x86_64、Dual-stack、1GB 套餐。禁用不需要的付费快照计划。
2. 实例名使用参数值；先查询同名资源，已存在就复用，不能再买一台。
3. 分配并立即绑定静态公网 IPv4；确认静态地址已附着目标实例，不遗留闲置地址。
4. 进入浏览器 SSH。若 CloudShell 显示账号验证未完成，直接走浏览器 SSH；不要反复删除 CloudShell 环境，也不要临时开放全网 SSH。
5. 更新系统包，核对安全更新；若提示需重启，在维护窗口重启并验证重新连接。设置系统安全更新，重启策略按用户授权执行。
6. 在用户自己完成 MFA 后，只核对绑定成功状态；不复制 MFA 密钥或恢复资料。

最终 Lightsail 入站规则：

| 协议与端口 | 来源 | 用途 |
|---|---|---|
| TCP 22 | Lightsail 浏览器 SSH；或已授权的固定来源 `/32` | 维护 |
| TCP 443 | 公网 IPv4 | Xray REALITY |
| TCP 8443 | 公网 IPv4 | HTTPS 订阅 |
| TCP 80 | 公网 IPv4 | ACME HTTP-01 验证；普通路径 404 |

本模板不开放公网 IPv6 入站，也不开放 UDP 443、管理面板、2019 或 Mihomo 控制端口。客户端 IPv6 与服务器入站防火墙是两件事，不要为此盲目关闭设备 IPv6。

若 UFW 已启用，按相同范围补齐规则；不要清空已有规则。22 的来源限制不能遗漏 IPv6。

## 5. 安装并生成服务端配置

以下命令仅在目标 Ubuntu 服务器执行。先确认 `uname -m` 为 `x86_64`，且 443/8443/80 没有其他服务占用。如果已有 Xray 或 Caddy，转到第 11 节做增量维护，不能执行首次安装覆盖。

```bash
uname -m
sudo ss -ltnp
sudo systemctl is-active xray clash-subscription || true
sudo install -d -m 700 /root/lightsail-proxy
sudo apt-get update
sudo apt-get install -y ca-certificates curl python3 python3-boto3 unzip
```

### 5.1 官方二进制

本案例验证版本：Xray `26.10.21`、Caddy `2.11.7`。下面固定为这组已测试版本；执行前查看官方 Release 是否撤回或出现必须升级的安全修复。升级时重新核对哈希和客户端兼容性，不能只改版本号。

进入已获授权的 root shell，在 `/root/lightsail-proxy` 执行；下载只使用官方 Release，校验失败立即停止。

```bash
set -euo pipefail
umask 077
cd /root/lightsail-proxy
curl -fL --retry 2 --connect-timeout 10 --max-time 180 \
  https://github.com/XTLS/Xray-core/releases/download/v26.10.21/Xray-linux-64.zip -o xray.zip
printf '%s  %s\n' 0eec3ed4163c273d8c8bf821f7d219e257921cf584aa3fb970715e458e631978 xray.zip | sha256sum -c -
unzip -p xray.zip xray > xray
install -m 755 xray /usr/local/bin/xray
curl -fL --retry 2 --connect-timeout 10 --max-time 180 \
  https://github.com/caddyserver/caddy/releases/download/v2.11.7/caddy_2.11.7_linux_amd64.tar.gz -o caddy.tar.gz
printf '%s  %s\n' 727b91701a392de6ebc5027509f548bf39979e5216340d0faed8fa5e69c84f8b caddy.tar.gz | sha256sum -c -
tar -xzf caddy.tar.gz caddy
install -m 755 caddy /usr/local/bin/caddy-subscription
/usr/local/bin/xray version
/usr/local/bin/caddy-subscription version
/usr/local/bin/xray tls ping www.amazon.com
```

最后一项应验证目标的 TLS 1.3、HTTP/2 和当前 REALITY 所需密钥交换能力。目标不可用就先定位 DNS/TLS；不要仅因模板写了 Amazon 就跳过验证。[Xray Release](https://github.com/XTLS/Xray-core/releases/tag/v26.10.21)、[Caddy Release](https://github.com/caddyserver/caddy/releases/tag/v2.11.7)

### 5.2 从单个 README 生成部署包

把本 README 保存为 `/root/lightsail-proxy/README.md`。AI 将附录 A 的 `render.py` 代码块写成同目录文件，并写入 `params.json`，替换真实静态 IP；参数文件不是公开仓库内容。

```json
{
  "REGION": "ap-southeast-1",
  "INSTANCE_NAME": "personal-proxy-sg",
  "SERVER_IPV4": "<从控制台读取的静态公网IPv4>",
  "SNI": "www.amazon.com",
  "QUOTA_BYTES": 2199023255552
}
```

```bash
cd /root/lightsail-proxy
chmod 600 params.json
python3 render.py
```

生成器从本文件附录提取所有模板，在服务器生成 UUID、short ID、X25519 密钥和 256-bit 订阅 token，保存在 `identity.json`，权限 `0600`。重复生成复用同一身份，不轮换凭据。私钥不离开服务器；生成结果在 `bundle/`。

### 5.3 启动 Xray

```bash
id xray >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin xray
install -d -o root -g xray -m 750 /etc/xray
install -o root -g xray -m 640 bundle/xray.json /etc/xray/config.json
install -m 644 bundle/xray.service /etc/systemd/system/xray.service
/usr/local/bin/xray run -test -config /etc/xray/config.json
systemctl daemon-reload
systemctl enable --now xray
systemctl is-active xray
ss -ltnp 'sport = :443'
```

服务使用无登录用户，只授予绑定低端口的能力；阻止通过代理访问私网、回环和云元数据地址。出口用 `freedom.streamSettings.sockopt.domainStrategy=UseIPv4`，避免继续使用本案例已遇到弃用提示的旧字段。

## 6. 客户端选型、Clash 配置和真实连通性

### 6.1 客户端

| 设备 | 默认做法 | 本案例证据 |
|---|---|---|
| macOS | 官方 Clash Verge Rev，使用维护中的 Mihomo 内核 | 2.5.8 / Mihomo 1.19.32 实测通过 |
| Android | 官方维护中的 Clash Meta for Android / 兼容 Mihomo 客户端；已有可用 Bettbox 可复用 | 用户实际使用 Bettbox 后确认连接及 Play 下载正常 |
| Windows | 官方 Clash Verge Rev，执行同样的连接验收 | 本案例没有 Windows 实机验收 |
| iOS | 支持当前 VLESS/REALITY 的客户端，先核对格式 | 本案例没有 iOS 实机验收 |

客户端从项目官方 Release 下载并核对发布者；不要只按 App 名字判断协议支持。[Clash Verge Rev](https://github.com/clash-verge-rev/clash-verge-rev/releases)、[Clash Meta for Android](https://github.com/MetaCubeX/ClashMetaForAndroid/releases)

**已复现的版本陷阱：** CMFA 2.10.4 内置的 Mihomo 1.18.8 在本节点上出现 `REALITY authentication failed`；同一配置用 Mihomo 1.19.32 成功。遇到这种日志先核对内核与 `support-x25519mlkem768`，不要反复改域名规则。这里是特定版本组合的实测结果，不是所有 REALITY 服务的通用最低版本声明。

### 6.2 导入与测试

1. 从服务器安全取回 `bundle/clash.yaml` 作为临时本地配置，文件权限 `0600`；不要复制 `identity.json` 或 Xray 服务端配置。
2. 在已有客户端新增独立配置，保留其他订阅、扩展脚本和选择状态。先 `mihomo -t -f clash.yaml`，再启用。
3. 模式设为 **规则**，`节点选择` 选 `AWS 新加坡`；Mac 开启 TUN。TUN 已开启时系统代理关闭也可以正常工作，不强制两个开关同时打开。
4. 测试必须通过新节点。独立测试内核可用 `127.0.0.1:17900`、关闭测试 TUN、绑定实际物理网卡，避免经旧机场转发；结束后停止测试进程。
5. 从真实客户端做下列检查，记录状态和实际出口。只显示延迟或配置解析成功，不算连接验收。

```bash
# 端口改成实际客户端 mixed-port；本模板为 7897。
curl --fail --max-time 20 -x http://127.0.0.1:7897 https://checkip.amazonaws.com
curl --max-time 20 -x http://127.0.0.1:7897 -o /dev/null -w '%{http_code}\n' https://www.google.com/generate_204
curl --max-time 20 -x http://127.0.0.1:7897 -o /dev/null -w '%{http_code}\n' https://www.youtube.com/
```

应分别得到服务器静态 IP、204、正常 YouTube 响应。另用支持 SOCKS5 UDP ASSOCIATE 的工具验证 XUDP：仅在隔离测试内核中临时使用 `rules: ["MATCH,AWS 新加坡"]`，查询 `8.8.8.8:53` 并收到响应，测试后销毁该临时配置。正式配置会拒绝未被 TUN 接管的 53 流量，不能用它执行这项绕过 DNS 模块的测试；普通 `curl` 无法证明 UDP 通。

### 6.3 业务分流与 DNS 固定出口

附录 `clash.yaml` 是唯一配置基线。业务规则按以下顺序执行：

```text
服务器 IP → DIRECT（防止连接节点自身形成循环）
Claude / Anthropic 官方域名及指定日志端点 → AWS 新加坡
已知 DoH / HTTPDNS、853 端口 → AWS 新加坡；未被 TUN 接管的 53 → REJECT
局域网域名 / 私有 IP → DIRECT
services.googleapis.cn → 节点选择
geolocation-!cn → 节点选择
cn 域名 / CN IP → DIRECT
其余 → 节点选择
```

`geolocation-!cn` 仍在 `cn` 前，避免集合重叠导致海外业务直连。Claude 使用显式规则固定到 `AWS 新加坡`，不随通用选择器切到 `DIRECT`；本配置覆盖官方域名及本案例观察到的两个日志端点，不改变 Claude Code/CLI 的第三方 API 设置，也不代表登录或订阅权限已通过。

DNS 采用同一组带 `#AWS 新加坡` 的 Cloudflare / Google DoH，统一用于 `nameserver`、`default-nameserver`、`proxy-server-nameserver`、`direct-nameserver`；Google 请求显式设置空 ECS。节点与 DoH 均使用 IP，启动不依赖直连 DNS。删除旧版国内直连 DNS policy，不再保留重复的按域名 DNS 列表。[Mihomo DNS 配置](https://wiki.metacubex.one/en/config/dns/)

**国内业务仍直连，但解析依赖 AWS。** AWS 不可用时，未缓存的国内、国外域名都会解析失败，不回退系统或明文 DNS；缓存、已有连接不一定立即失效。不能把这一行为写成“代理停了国内上网也不受影响”。若内网名称只由路由器或企业 DNS 提供，本基线不会自动查询它，先确认所需内网名称再设置精确例外。

通过真实连接日志核对 Google、GitHub、Claude、国内站点和局域网地址的出口；系统 DNS 显示一个公共地址不等于请求已从物理网卡泄漏，需结合 TUN 接管和抓包判断。Geo 数据每 24 小时更新，首次加载须成功。

### 6.4 Google Play 无法下载

本案例表现：规则模式下载不动，全局模式可下载。连接日志显示下载 CDN 已走代理，但 `services.googleapis.cn` 被国内域名规则直连。

已采用的最小修复：把 `DOMAIN,services.googleapis.cn,节点选择` 放到 `GEOSITE,cn,DIRECT` 前面；模板已包含。随后更新**服务器订阅源文件**，手机更新订阅、断开重连，在规则模式真实下载一个应用验证。

不把全部 `google.cn` 一刀切代理，不先清除 Play 服务数据。若全局模式也失败，先处理节点连接、客户端协议兼容和账号/设备问题，这条规则不能替代根因检查。

### 6.5 macOS DNS 防护与回退

分两层实施：订阅中的 `tun.dns-hijack` 同时接管 UDP 和 TCP 53；Mac 本机 PF 只阻止物理 `en*` / `bridge*` 接口上的 TCP/UDP 53、853。**禁止使用 `on ! lo0`**：它也会挡住 `utun*`，曾造成 TUN 内 DNS 失败和普通 HTTPS 连接超时。不要改动全局 PF 主规则、清空其他 anchor 或刷新全部连接状态。

这项 PF 防护是 Mac 本机设置，不能随订阅下发给手机。它不识别所有应用自带的 HTTPS DNS；已知 DoH/HTTPDNS 用附录规则处理，未知 443 DNS 仍按普通业务规则匹配。Android 的 Private DNS 也可能绕过 TUN DNS 接管，应单独核对实际客户端设置。[Mihomo TUN 说明](https://wiki.metacubex.one/en/config/inbound/tun/)

实施顺序：

1. 先在隔离内核验证订阅，再在真实 TUN 下验证国内外 HTTPS 和 TCP/UDP DNS。仅返回 fake IP 不能证明上游解析成功；另查内核 `/dns/query` 的真实答案或完成带证书校验的 HTTPS。
2. 读取客户端**最终生效配置**。Clash Verge Rev 的全局 DNS 覆盖、订阅 Merge/Script 可能覆盖源 YAML；只调整冲突项，保留其他订阅。不要为套用模板把 Wi-Fi DNS 永久写死为 `127.0.0.1`；局域网 DNS 不一定被 macOS TUN 自动接管。
3. 说明防护范围、关闭代理后的解析失败行为和下方回退路径，获得安装授权。把生成的 `bundle/macos-dns-guard.sh`、`bundle/local.clash-dns-guard.plist`、`bundle/macos-dns-rollback.sh` 安全复制到 Mac 私密目录。不要把整个含节点凭据的 bundle 上传公共位置。
4. 已有同名防护时先备份并增量更新，不执行下面的首次安装段。新增 USB 网卡后重新运行 helper 并复验；开机时 LaunchDaemon 会重新枚举网卡。其他接口命名不在本模板覆盖范围。

首次安装：在 Mac 已授权的 root shell 中，进入上述三个文件所在目录执行。先启动独立的 **120 秒自动回退**，验证完再提交；以下命令不修改系统 DNS。

```bash
set -eu
umask 077
trial=/var/run/local.clash-dns-guard.trial
for target in /usr/local/libexec/clash-dns-guard \
  /etc/pf.anchors/local.clash-dns-guard \
  /Library/LaunchDaemons/local.clash-dns-guard.plist \
  /var/run/local.clash-dns-guard.token; do
  test ! -e "$target" || { echo 'Existing guard found; use incremental maintenance.'; exit 1; }
done
pfctl -sr | grep -F 'anchor "com.apple/*"' >/dev/null
# 先检查现有 PF 顺序；前置 quick pass 或其他 VPN 规则需单独验证。
mkdir -m 700 "$trial"
install -o root -g wheel -m 700 macos-dns-rollback.sh "$trial/rollback.sh"
nohup /bin/sh "$trial/rollback.sh" --watch > "$trial/watch.log" 2>&1 < /dev/null &
install -d -o root -g wheel -m 755 /usr/local/libexec
install -o root -g wheel -m 755 macos-dns-guard.sh /usr/local/libexec/clash-dns-guard
install -o root -g wheel -m 644 local.clash-dns-guard.plist /Library/LaunchDaemons/local.clash-dns-guard.plist
/usr/local/libexec/clash-dns-guard
pfctl -a com.apple/000.clash-dns-guard -sr
```

在 120 秒内验证：普通国内/国外 HTTPS 正常；发往当前系统 DNS 的 UDP/TCP 查询都能被 TUN 处理；使用绑定物理接口的 socket 发往 53/853 被阻止。用 `tcpdump -ni <实际物理接口> 'dst port 53 or dst port 853'` 同时抓包，不能把“应用请求失败”单独作为无泄漏证据。默认路由下的 `dig @8.8.8.8` 可能被 TUN 接管，不是物理绕过测试。

全通过后，在同一 root shell 提交；争抢同一 `decision` 目录使超时回退与提交只能成功一个。若 `mkdir` 失败，读取 `result` 和日志，不要强行写成功。超时或任一验收失败，运行回退脚本，只卸载本次首次安装。

```bash
# 仅在所有实时检查通过且尚未超时后执行。
set -eu
trial=/var/run/local.clash-dns-guard.trial
mkdir "$trial/decision"
if ! launchctl bootstrap system /Library/LaunchDaemons/local.clash-dns-guard.plist; then
  /bin/sh "$trial/rollback.sh" --rollback
  exit 1
fi
printf 'COMMITTED\n' > "$trial/result"
```

```bash
# 本次首次安装的手动回退；不会关闭全局 PF 或改动其他规则。
sudo /bin/sh /var/run/local.clash-dns-guard.trial/rollback.sh --rollback
```

提交后再核对 `launchctl print system/local.clash-dns-guard`、anchor 和 helper 的网卡列表。重启内核、切换订阅、重启 Mac 各自复验；未执行的项目写“未测”。停代理后的失败保护测试优先使用隔离内核，不为文档校验中断正在使用的网络。

### 6.6 与其他订阅共存

AWS 订阅的固定 IP 无需直连 bootstrap。其他订阅若用域名连接节点，不能照搬“节点域名也经该节点解析”，否则会循环依赖。只在该订阅的 Merge 中把 `default-nameserver` 与 `proxy-server-nameserver` 设置为 IP 形式的加密 bootstrap（如 `https://223.5.5.5/dns-query#DIRECT`）；普通 `nameserver`、`direct-nameserver` 仍经该订阅已验证的节点，不能保留会抢先匹配的旧直连 DNS policy。此分支允许节点启动所需的直连加密查询，保护范围与 AWS 基线不同。

不要只凭 HTTP 204 延迟测速选 DNS 出口：本案例曾出现测速正常、真实 TLS 失败的节点。用多个国内外域名完成证书校验和真实解析，再固定可用节点；切换订阅及重启后重新检查。不要把某个机场节点名或一次成功写成全部节点可用。

## 7. 生成可自动更新的 HTTPS 订阅

443 已给 Xray，订阅固定使用 8443；80 用于 HTTP-01 自动续期。无域名时，Caddy 通过 Let’s Encrypt 为静态公网 IP 申请短期证书。证书有效期约 160 小时，必须保持续期服务与 80 端口可达。[IP 证书说明](https://letsencrypt.org/2026/01/15/6day-and-ip-general-availability)

先展示拟开放的 80/8443 及当前 [Let’s Encrypt 订阅者协议](https://letsencrypt.org/repository/)，取得对应确认，再修改入站规则和启动证书申请。不要用自签证书加 `skip-cert-verify` 代替正常 HTTPS。

### 7.1 安装订阅服务并先用测试 CA

以下仍在 `/root/lightsail-proxy` 的 root shell 执行：

```bash
id clash-sub >/dev/null 2>&1 || useradd --system --home-dir /var/lib/clash-subscription --shell /usr/sbin/nologin clash-sub
install -d -o root -g clash-sub -m 750 /etc/clash-subscription /srv/clash-subscription
install -o root -g clash-sub -m 640 bundle/clash.yaml /srv/clash-subscription/clash.yaml
# 首次未取到 AWS 指标时不发布虚假的“已用 0”；该文件此时只有注释。
install -o root -g clash-sub -m 640 bundle/traffic-header.caddy /etc/clash-subscription/traffic-header.caddy
install -o root -g clash-sub -m 640 bundle/Caddyfile.staging /etc/clash-subscription/Caddyfile
install -m 644 bundle/clash-subscription.service /etc/systemd/system/clash-subscription.service
/usr/local/bin/caddy-subscription validate --config /etc/clash-subscription/Caddyfile --adapter caddyfile
systemctl daemon-reload
systemctl enable --now clash-subscription
systemctl is-active clash-subscription
```

通过服务日志核对 staging 证书已签发；日志可能包含私密请求路径，不整段公开。浏览器遇到不受信任的测试证书时不要绕过警告，也不要把测试 URL 导入正式客户端。

### 7.2 切换正式 CA

```bash
install -o root -g clash-sub -m 640 bundle/Caddyfile /etc/clash-subscription/Caddyfile
/usr/local/bin/caddy-subscription validate --config /etc/clash-subscription/Caddyfile --adapter caddyfile
systemctl restart clash-subscription
systemctl is-active clash-subscription xray
```

`bundle/subscription-url.txt` 保存最终 URL，形如 `https://<静态IP>:8443/<随机token>/clash.yaml`。持有该 URL 就能读取节点凭据，只向用户私下交付，不提交到 GitHub 或在线订阅转换站。

验证：

1. 用正常 TLS 校验下载，证书 IP SAN 匹配、正式颁发者可信；不能加 `-k`。
2. 订阅返回 200，正文 SHA-256 与 `/srv/clash-subscription/clash.yaml` 相同。
3. HTTPS 根路径、`/clash.yaml`、错误 token 路径返回 404；HTTP 80 普通路径返回 404。
4. 日志存在续期计划；“已安排续期”与“未来续期已发生”分开报告。
5. 下载得到的 YAML 再经独立 Mihomo 导入并联网测试，Xray 仍正常。

Caddy 必须保留 `default_sni <静态IP>`，解决以 IP 连接、客户端不发送 SNI 的情况。关闭管理 API 后，本文通过 `SIGUSR1` 重载原配置；服务必须以 `caddy run --config ...` 启动，不能混用 API 加载另一份配置。[Caddy 命令与信号](https://caddyserver.com/docs/command-line)、[TLS 配置](https://caddyserver.com/docs/caddyfile/directives/tls)

## 8. AWS 月流量统计接入 Clash

### 8.1 统计口径

统计当前 UTC 月初到现在的 **NetworkIn + NetworkOut，单位 Bytes，统计 Sum，period=3600**，每 15 分钟重新取整个月数据。机器重启不清零；下一 UTC 月自动换查询范围，UTC+8 对应每月 1 日 08:00。[Lightsail 指标 API](https://docs.aws.amazon.com/lightsail/2016-11-28/api-reference/API_GetInstanceMetricData.html)

这显示服务器总网络用量，Mac 和手机共享，不是单个设备用量。代理转发的入站与出站都计入额度；2TB 不等于能下载 2TB 文件。它是运维用量显示，**不是账单计算器**：同区域同套餐多实例的额度聚合、免费私网流量等需看 AWS 账单。本文按单实例部署。

新加坡超额公网出站目前为 **0.12 美元/GB**；入站与出站都消耗额度，但超额入站本身不收费。显示满额不会自动断网，本手册没有安装自动停机功能。[流量计费规则](https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-faq-data-transfer-allowance.html)

### 8.2 创建专用只读 IAM 身份

先把附录生成的 `iam-policy.json` 给用户审阅。获得新增长期凭据的授权后：

1. 创建专用 IAM 用户 `lightsail-traffic-reader`，**不创建控制台密码**。
2. 只附加本文策略，action 为 `lightsail:GetInstanceMetricData`；区域限新加坡，来源 IP 限服务器静态公网 IPv4 `/32`。
3. 此 action 不支持按实例 ARN 授权，所以 `Resource` 必须为 `*`。它可以读取账号在该区域的指标，程序仅查询指定实例；不能声称 IAM 已隔离到单台实例。[权限参考](https://docs.aws.amazon.com/service-authorization/latest/reference/list_lightsail.html)
4. 创建一组 Access Key，仅用于服务器采集。不要使用账号管理员 Key，也不要追加其他读写权限来消除报错。
5. 通过已有安全会话把 Key 写到服务器 `/etc/clash-subscription/traffic-credentials.json`，属主 `root:root`、权限 `0600`。使用不回显的输入或安全文件传输，不能把密钥拼进命令行参数、聊天、截图或终端历史。浏览器 SSH 的输入框可能保留粘贴内容；取证时只截取脱敏结果。

凭据文件结构：

```json
{
  "access_key_id": "<专用AccessKeyId>",
  "secret_access_key": "<专用SecretAccessKey>"
}
```

### 8.3 启动采集

```bash
install -d -m 755 /usr/local/lib/clash-subscription
install -m 755 bundle/meter.py /usr/local/lib/clash-subscription/meter.py
install -m 644 bundle/lightsail-traffic.service /etc/systemd/system/lightsail-traffic.service
install -m 644 bundle/lightsail-traffic.timer /etc/systemd/system/lightsail-traffic.timer
chown root:root /etc/clash-subscription/traffic-credentials.json
chmod 600 /etc/clash-subscription/traffic-credentials.json
systemctl daemon-reload
systemctl start lightsail-traffic.service
systemctl show lightsail-traffic.service -p Result -p ExecMainStatus
systemctl enable --now lightsail-traffic.timer
systemctl list-timers lightsail-traffic.timer --no-pager
```

首个采集必须成功再宣布完成。指标请求失败或数据异常时保留上次快照；每月开始后的前 15 分钟若 AWS 尚无指标，允许暂报新月份 0，其他时段空数据报错并保留旧值。两种情况均需核对状态文件时间，不能填手工估计值冒充实测。

响应头格式：

```text
Subscription-Userinfo: upload=<NetworkOut字节>; download=<NetworkIn字节>; total=2199023255552; expire=0
profile-update-interval: 1
```

这里 upload/download 按服务器视角映射，Clash 卡片使用两者总和。`expire=0` 不伪造套餐到期日，**不要把下个月月初当订阅过期时间**。Caddy 只重载统计头，订阅正文保持不变。

核对 `/etc/clash-subscription/traffic-state.json` 的月份、更新时间和合计；实际 HTTPS 响应头应一致。再用相同凭据请求 `GetInstances`，预期 `AccessDenied`，验证没有意外获得宽泛权限。不要为这项验证给专用用户增加权限。

## 9. 切换远程订阅并验证显示

1. Mac 原配置若是“本地文件”，改为同一 URL 的**远程订阅**；本地配置不会读取订阅响应头。优先通过客户端 UI 修改，保留 UID、扩展脚本、规则覆盖和其他订阅。
2. 开启自动更新，间隔 60 分钟；证书验证保持开启。服务端 `profile-update-interval: 1` 的单位是小时，客户端已有设置可能优先，须在 UI 核对。
3. 手动更新一次，卡片应出现“本月已用 / 2.00 TB”。描述可写“每月 1 日 08:00 重置”，不是订阅到期时间。
4. Android 添加或更新同一 URL，选择 AWS 节点，规则模式断开重连；核对连接、Play 下载和流量卡片。
5. 采集约每 15 分钟更新，客户端在订阅刷新时读取，**不是实时推送仪表盘**。某客户端不展示该响应头时，分别报告“服务端已返回”与“该客户端未显示”。
6. 保留三份相互核对的证据：AWS 统计状态、HTTPS `Subscription-Userinfo`、客户端卡片；记录更新时间。规则/DNS 更新只替换订阅 YAML，继续复用第 8 节同一个采集服务和定时器，不重复安装统计功能。

## 10. 验收记录

AI 按实际结果填写，未知项不能写通过：

| 检查 | 通过条件 |
|---|---|
| 账号与费用 | 实例套餐、地区、赠金产品范围与到期日已核对 |
| 网络入口 | 443/8443/80 与授权一致；22 未全网开放 |
| Xray | 配置测试通过、服务 active/enabled、443 监听 |
| 客户端 TCP/UDP | 正确出口、Google 204、YouTube 可访问、UDP DNS 收到响应 |
| 分流和 DNS | 国内业务 DIRECT、Claude 与 DoH 固定 AWS、Play 入口命中指定规则 |
| DNS 失败保护 | 隔离内核中的 AWS 不可用且选择器为 DIRECT 时，真实 DNS 查询失败且无直连回退 |
| Mac PF | TUN TCP/UDP DNS 可用；物理接口 53/853 绕过请求被阻止，抓包无出站 |
| 切换与重启 | 分别记录订阅切换、内核重启、整机重启结果，未执行不得写通过 |
| 手机 Play | 规则模式实际完成一次应用下载 |
| 订阅 | 可信 TLS、200、正文一致、错误路径 404 |
| 续期 | 正式证书、有效期和自动续期计划可查 |
| 流量 | 两个 AWS 指标 Sum、月份正确、响应头与状态文件一致 |
| 权限 | 凭据 0600、专用 API 允许、无关 API 被拒绝 |
| UI | Mac 远程订阅卡片出现用量；手机单独核对 |

本案例已跑通服务器、Mac、手机连接和 Play 下载；流量响应头和 Mac 远程订阅用量信息已有证据，手机流量卡片仍待实机核对。后续完成了 AWS 固定 DNS、物理网卡防护及 TUN 连通性修复；各订阅切换与内核测试的结果需逐项保留，不能推广成所有节点或整机重启均通过。仓库回归使用脱敏配置，不重新部署服务器或修改本机网络。

## 11. 维护、续跑与故障定位

### 更新规则

1. 备份 `/srv/clash-subscription/clash.yaml`，准备 `.new` 文件，使用 Mihomo 校验。
2. 保持原 UUID、公钥、short ID、订阅 token 和地址不变；只改本次规则/DNS。
3. 同文件系统原子替换，属主 `root:clash-sub`、权限 `0640`；静态 YAML 不需要重启 Xray。
4. 下载原订阅 URL 核对 SHA-256，Mac 和手机分别更新订阅。**只改 Mac 本地文件，手机不会自动得到修改。**

### 续跑与回退

先读状态、检查文件和服务，再执行未完成阶段。首次安装命令不用于覆盖已有部署。恢复时只使用本次保存的旧配置，先验证再重载对应服务；不删除实例、静态 IP、其他订阅或 AWS 组织策略。不要重新生成 `identity.json`，否则现有客户端会失效。

若静态公网 IP 发生变化，同步修改客户端地址、节点直连规则、Caddy 地址及证书、IAM 来源 IP 条件，并重新完成订阅与流量检查。

| 现象 | 先核对 | 修复方向 |
|---|---|---|
| CloudShell 无法创建环境 | 新账号验证状态 | 使用 Lightsail 浏览器 SSH |
| `REALITY authentication failed` | 内核版本、UUID、公钥、short ID、SNI、混合密钥交换支持 | 更新兼容客户端；不要先改规则 |
| 全局正常、规则模式 Play 失败 | `services.googleapis.cn` 的实际命中规则 | 把精确域名规则放到 CN 规则前，并更新服务器订阅 |
| 海外页面仍出现国内 DNS/出口 | 最终生效 DNS、覆盖脚本、真实连接与物理抓包 | 使用固定 AWS DoH；区分系统 DNS 显示值与实际出站 |
| 加固后国内外 HTTPS 都超时 | PF 是否包含 `! lo0` 或 `utun*`、TUN TCP/UDP DNS | 回退本次 PF，再只对物理接口加载；不要盲目修改业务分流 |
| 其他订阅无法解析或测速绿但 TLS 失败 | 节点域名 bootstrap、选中节点的真实 TLS | 按 6.6 节在该订阅 Merge 修复并单独验收 |
| 订阅证书错误 | 正式 CA、IP SAN、default_sni、80 连通性 | 修复签发或续期，不关闭证书校验 |
| 没有流量卡片 | 本地/远程配置、实际响应头、客户端支持 | 改成远程订阅并刷新 |
| 流量不更新 | timer、service Result、状态文件时间、SourceIp 条件 | 修复采集；失败保留旧值，不清零 |
| 国家显示不是预期 | 代理出口 IP 与 ASN、IP 库、站点账号/语言 | 分别验证；AWS 是数据中心 IP，不承诺住宅 IP 或改变账号地区 |

交付给用户：私密订阅 URL、配置文件、费用与赠金核实结果、逐项验收状态、需要用户完成的设备操作。公开仓库只保存本 README 与脱敏检查工具。

## 附录 A：生成器

以下 `<!-- file: ... -->` 标记用于提取模板。AI 把本节代码保存成 `render.py`；其余模板由它自动生成。

<!-- file: render.py -->
```python
#!/usr/bin/env python3
import ipaddress
import json
import os
import re
import secrets
import subprocess
import uuid
from pathlib import Path


def extract(text):
    pattern = r"<!-- file: ([\w.-]+) -->\n```[^\n]*\n(.*?)\n```"
    return dict(re.findall(pattern, text, re.S))


def render(text, values):
    def replace(match):
        return str(values[match.group(1)])
    return re.sub(r"@@([A-Z0-9_]+)@@", replace, text)


def main():
    os.umask(0o077)
    base = Path(__file__).resolve().parent
    params = json.loads((base / "params.json").read_text())
    ip = ipaddress.ip_address(params["SERVER_IPV4"])
    if ip.version != 4 or not ip.is_global:
        raise ValueError("SERVER_IPV4 must be the attached public static IPv4")
    for key in ("REGION", "INSTANCE_NAME", "SNI"):
        if not re.fullmatch(r"[A-Za-z0-9.-]+", params[key]):
            raise ValueError(f"Invalid {key}")
    if type(params["QUOTA_BYTES"]) is not int or params["QUOTA_BYTES"] <= 0:
        raise ValueError("QUOTA_BYTES must be a positive integer")
    identity_path = base / "identity.json"
    if identity_path.exists():
        identity = json.loads(identity_path.read_text())
    else:
        lines = subprocess.check_output(["/usr/local/bin/xray", "x25519"], text=True).splitlines()
        keys = {k.replace(" ", "").lower(): v.strip()
                for line in lines if ":" in line for k, v in [line.split(":", 1)]}
        public = keys.get("password(publickey)") or keys.get("publickey")
        if not public or not keys.get("privatekey"):
            raise ValueError("Unrecognized Xray key output; inspect labels without printing keys")
        identity = {"PRIVATE_KEY": keys["privatekey"], "PUBLIC_KEY": public,
                    "UUID": str(uuid.uuid4()), "SHORT_ID": secrets.token_hex(8),
                    "SUB_TOKEN": secrets.token_urlsafe(32)}
        with identity_path.open("x") as stream:
            json.dump(identity, stream, indent=2)
    identity_path.chmod(0o600)
    values = {**params, **identity}
    templates = extract((base / "README.md").read_text())
    required = {"xray.json", "xray.service", "clash.yaml", "Caddyfile",
                "clash-subscription.service", "traffic-header.caddy", "meter.py",
                "lightsail-traffic.service", "lightsail-traffic.timer", "iam-policy.json",
                "macos-dns-guard.sh", "local.clash-dns-guard.plist", "macos-dns-rollback.sh"}
    if not required.issubset(templates):
        raise ValueError(f"Missing templates: {sorted(required - templates.keys())}")
    bundle = base / "bundle"
    bundle.mkdir(mode=0o700, exist_ok=True)
    for name in sorted(required):
        destination = bundle / name
        destination.write_text(render(templates[name], values) + "\n")
        destination.chmod(0o600)
    staging = (bundle / "Caddyfile").read_text().replace(
        "acme-v02.api.letsencrypt.org", "acme-staging-v02.api.letsencrypt.org")
    (bundle / "Caddyfile.staging").write_text(staging)
    (bundle / "subscription-url.txt").write_text(
        f'https://{params["SERVER_IPV4"]}:8443/{identity["SUB_TOKEN"]}/clash.yaml\n')
    print("Bundle generated; credentials and subscription URL were not printed.")


if __name__ == "__main__":
    main()
```

## 附录 B：服务、订阅与统计模板

配置中的 `@@...@@` 由生成器替换，不要手工把真实值回填到公开 README。

### `xray.json`

<!-- file: xray.json -->
```json
{
  "log": {
    "loglevel": "warning"
  },
  "inbounds": [
    {
      "tag": "vless-reality",
      "listen": "0.0.0.0",
      "port": 443,
      "protocol": "vless",
      "settings": {
        "clients": [
          {
            "id": "@@UUID@@",
            "flow": "xtls-rprx-vision"
          }
        ],
        "decryption": "none"
      },
      "streamSettings": {
        "network": "raw",
        "security": "reality",
        "realitySettings": {
          "show": false,
          "target": "@@SNI@@:443",
          "serverNames": [
            "@@SNI@@"
          ],
          "privateKey": "@@PRIVATE_KEY@@",
          "shortIds": [
            "@@SHORT_ID@@"
          ]
        }
      }
    }
  ],
  "outbounds": [
    {
      "tag": "direct",
      "protocol": "freedom",
      "streamSettings": {
        "sockopt": {
          "domainStrategy": "UseIPv4"
        }
      }
    },
    {
      "tag": "blocked",
      "protocol": "blackhole"
    }
  ],
  "routing": {
    "domainStrategy": "IPIfNonMatch",
    "rules": [
      {
        "type": "field",
        "ip": [
          "0.0.0.0/8",
          "10.0.0.0/8",
          "100.64.0.0/10",
          "127.0.0.0/8",
          "169.254.0.0/16",
          "172.16.0.0/12",
          "192.168.0.0/16",
          "224.0.0.0/4",
          "240.0.0.0/4",
          "::/128",
          "::1/128",
          "fc00::/7",
          "fe80::/10",
          "ff00::/8"
        ],
        "outboundTag": "blocked"
      }
    ]
  }
}
```

### `xray.service`

<!-- file: xray.service -->
```ini
[Unit]
Description=Xray personal proxy
After=network-online.target
Wants=network-online.target

[Service]
User=xray
Group=xray
ExecStart=/usr/local/bin/xray run -config /etc/xray/config.json
Restart=on-failure
RestartSec=3
LimitNOFILE=65536
AmbientCapabilities=CAP_NET_BIND_SERVICE
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true

[Install]
WantedBy=multi-user.target
```

### `clash.yaml`

<!-- file: clash.yaml -->
```yaml
---
mixed-port: 7897
allow-lan: false
mode: rule
log-level: warning
ipv6: true
profile:
  store-selected: true
dns:
  enable: true
  ipv6: true
  default-nameserver:
  - https://1.1.1.1/dns-query#AWS 新加坡
  - https://8.8.8.8/dns-query#AWS 新加坡&ecs=0.0.0.0/0&ecs-override=true
  enhanced-mode: fake-ip
  fake-ip-range: 198.18.0.1/16
  use-hosts: true
  nameserver:
  - https://1.1.1.1/dns-query#AWS 新加坡
  - https://8.8.8.8/dns-query#AWS 新加坡&ecs=0.0.0.0/0&ecs-override=true
  fake-ip-range6: 2001:2::0/64
  use-system-hosts: false
  proxy-server-nameserver:
  - https://1.1.1.1/dns-query#AWS 新加坡
  - https://8.8.8.8/dns-query#AWS 新加坡&ecs=0.0.0.0/0&ecs-override=true
  direct-nameserver:
  - https://1.1.1.1/dns-query#AWS 新加坡
  - https://8.8.8.8/dns-query#AWS 新加坡&ecs=0.0.0.0/0&ecs-override=true
proxies:
- name: AWS 新加坡
  type: vless
  server: "@@SERVER_IPV4@@"
  port: 443
  uuid: "@@UUID@@"
  flow: xtls-rprx-vision
  tls: true
  servername: "@@SNI@@"
  client-fingerprint: chrome
  network: tcp
  udp: true
  packet-encoding: xudp
  reality-opts:
    public-key: "@@PUBLIC_KEY@@"
    short-id: "@@SHORT_ID@@"
    support-x25519mlkem768: true
proxy-groups:
- name: 节点选择
  type: select
  proxies:
  - AWS 新加坡
  - DIRECT
rules:
- IP-CIDR,@@SERVER_IPV4@@/32,DIRECT,no-resolve
- DOMAIN-SUFFIX,anthropic.com,AWS 新加坡
- DOMAIN-SUFFIX,claude.ai,AWS 新加坡
- DOMAIN-SUFFIX,claude.com,AWS 新加坡
- DOMAIN-SUFFIX,claude.app,AWS 新加坡
- DOMAIN-SUFFIX,claudeusercontent.com,AWS 新加坡
- DOMAIN-SUFFIX,claudemcpcontent.com,AWS 新加坡
- DOMAIN,http-intake.logs.us5.datadoghq.com,AWS 新加坡
- DOMAIN,browser-intake-us5-datadoghq.com,AWS 新加坡
- GEOSITE,category-doh,AWS 新加坡
- GEOSITE,category-httpdns-cn,AWS 新加坡
- DST-PORT,53,REJECT
- DST-PORT,853,AWS 新加坡
- IP-CIDR,1.1.1.1/32,AWS 新加坡,no-resolve
- IP-CIDR,1.0.0.1/32,AWS 新加坡,no-resolve
- IP-CIDR,8.8.8.8/32,AWS 新加坡,no-resolve
- IP-CIDR,8.8.4.4/32,AWS 新加坡,no-resolve
- IP-CIDR,223.5.5.5/32,AWS 新加坡,no-resolve
- IP-CIDR,223.6.6.6/32,AWS 新加坡,no-resolve
- IP-CIDR,119.29.29.29/32,AWS 新加坡,no-resolve
- GEOSITE,private,DIRECT
- GEOIP,private,DIRECT,no-resolve
- DOMAIN,services.googleapis.cn,节点选择
- GEOSITE,geolocation-!cn,节点选择
- GEOSITE,cn,DIRECT
- GEOIP,CN,DIRECT
- MATCH,节点选择
geo-auto-update: true
geo-update-interval: 24
tun:
  dns-hijack:
  - any:53
  - tcp://any:53
```

### `Caddyfile`

<!-- file: Caddyfile -->
```caddyfile
{
    admin off
    persist_config off
    auto_https disable_redirects
    default_sni @@SERVER_IPV4@@
    servers {
        protocols h1 h2
    }
}

http://:80 {
    bind 0.0.0.0
    respond 404
}

https://@@SERVER_IPV4@@:8443 {
    bind 0.0.0.0
    tls {
        issuer acme {
            dir https://acme-v02.api.letsencrypt.org/directory
            profile shortlived
            disable_tlsalpn_challenge
        }
    }
    @subscription {
        path /@@SUB_TOKEN@@/clash.yaml
        method GET HEAD
    }
    handle @subscription {
        root * /srv/clash-subscription
        rewrite * /clash.yaml
        header {
            Content-Type application/yaml
            Cache-Control "no-store"
            profile-update-interval 1
            Content-Disposition "attachment; filename=AWS-SG-Clash.yaml"
            import /etc/clash-subscription/traffic-header.caddy
        }
        file_server
    }
    handle {
        respond 404
    }
}
```

### `clash-subscription.service`

<!-- file: clash-subscription.service -->
```ini
[Unit]
Description=Private Clash HTTPS subscription
After=network-online.target
Wants=network-online.target

[Service]
Type=notify
User=clash-sub
Group=clash-sub
Environment=HOME=/var/lib/clash-subscription
ExecStart=/usr/local/bin/caddy-subscription run --config /etc/clash-subscription/Caddyfile --adapter caddyfile
Restart=on-failure
RestartSec=5
StateDirectory=clash-subscription
StateDirectoryMode=0700
AmbientCapabilities=CAP_NET_BIND_SERVICE
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
UMask=0077

[Install]
WantedBy=multi-user.target
```

### `traffic-header.caddy`

<!-- file: traffic-header.caddy -->
```caddyfile
# No usage header until the first successful AWS metrics query.
```

### `meter.py`

<!-- file: meter.py -->
```python
#!/usr/bin/python3
"""Publish AWS Lightsail UTC-month network totals to the private subscription."""
import json
import math
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REGION = "@@REGION@@"
INSTANCE = "@@INSTANCE_NAME@@"
TOTAL = @@QUOTA_BYTES@@
CONFIG_DIR = Path("/etc/clash-subscription")


def atomic_write(path, content):
    previous = path.stat() if path.exists() else None
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".traffic-")
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if previous is not None:
            os.chmod(name, previous.st_mode & 0o777)
            os.chown(name, previous.st_uid, previous.st_gid)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def update(client, now, header, state):
    now = now.astimezone(timezone.utc)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    counts = {}
    for metric in ("NetworkIn", "NetworkOut"):
        response = client.get_instance_metric_data(
            instanceName=INSTANCE, metricName=metric, period=3600,
            startTime=start, endTime=now, unit="Bytes", statistics=["Sum"])
        points = response["metricData"]
        if not points and (now - start).total_seconds() >= 900:
            raise ValueError(f"No current-month {metric} data; retaining previous snapshot")
        values = [p["sum"] for p in points]
        if any(not math.isfinite(n) or n < 0 for n in values):
            raise ValueError(f"Invalid {metric} total")
        counts[metric] = round(sum(values))
    snapshot = {
        "source": "AWS Lightsail NetworkIn + NetworkOut (Sum)",
        "instance": INSTANCE, "region": REGION,
        "month": start.strftime("%Y-%m"), "updated_at": now.isoformat(),
        "network_in_bytes": counts["NetworkIn"],
        "network_out_bytes": counts["NetworkOut"],
        "used_bytes": sum(counts.values()), "total_bytes": TOTAL,
    }
    value = (f'Subscription-Userinfo "upload={counts["NetworkOut"]}; '
             f'download={counts["NetworkIn"]}; total={TOTAL}; expire=0"\n')
    atomic_write(state, json.dumps(snapshot, indent=2) + "\n")
    atomic_write(header, value)
    return snapshot


def main():
    import boto3
    from botocore.config import Config

    credentials = json.loads((CONFIG_DIR / "traffic-credentials.json").read_text())
    client = boto3.client(
        "lightsail", region_name=REGION,
        aws_access_key_id=credentials["access_key_id"],
        aws_secret_access_key=credentials["secret_access_key"],
        config=Config(connect_timeout=10, read_timeout=30,
                      retries={"mode": "standard", "max_attempts": 3}))
    snapshot = update(client, datetime.now(timezone.utc),
                      CONFIG_DIR / "traffic-header.caddy",
                      CONFIG_DIR / "traffic-state.json")
    subprocess.run(["systemctl", "kill", "--kill-whom=main", "--signal=USR1",
                    "clash-subscription.service"], check=True)
    print(f'{snapshot["month"]}: {snapshot["used_bytes"]} / {TOTAL} bytes')


if __name__ == "__main__":
    main()
```

### `lightsail-traffic.service`

<!-- file: lightsail-traffic.service -->
```ini
[Unit]
Description=Update Lightsail monthly traffic in Clash subscription
After=network-online.target clash-subscription.service
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /usr/local/lib/clash-subscription/meter.py
TimeoutStartSec=180
UMask=0077
```

### `lightsail-traffic.timer`

<!-- file: lightsail-traffic.timer -->
```ini
[Unit]
Description=Refresh Lightsail traffic every 15 minutes

[Timer]
OnCalendar=*-*-* *:00/15:00
Persistent=true
RandomizedDelaySec=30

[Install]
WantedBy=timers.target
```

### `iam-policy.json`

<!-- file: iam-policy.json -->
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadLightsailMetricsFromProxyOnly",
      "Effect": "Allow",
      "Action": "lightsail:GetInstanceMetricData",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "@@REGION@@"
        },
        "IpAddress": {
          "aws:SourceIp": "@@SERVER_IPV4@@/32"
        }
      }
    }
  ]
}
```

## 附录 C：Mac 本机 DNS 防护模板

只按第 6.5 节在 Mac 安装，不在 Ubuntu 服务器执行。PF helper 每次运行重新枚举物理接口，未匹配到接口时停止。

### `macos-dns-guard.sh`

<!-- file: macos-dns-guard.sh -->
```sh
#!/bin/sh
set -eu
PATH=/usr/bin:/bin:/usr/sbin:/sbin
export PATH
render_rules() {
  awk '/^(en|bridge)[0-9]+$/ {
    if (n++) interfaces = interfaces ", "; interfaces = interfaces $0
  } END {
    if (!n) exit 1
    printf "block drop out quick on { %s } proto { tcp udp } from any to any port { 53, 853 }\n", interfaces
  }'
}
if [ "${1:-}" = --print-rules ]; then
  shift
  printf '%s\n' "$@" | render_rules
  exit
fi
[ "$#" -eq 0 ]
[ "$(id -u)" -eq 0 ]
anchor=com.apple/000.clash-dns-guard
rules=/etc/pf.anchors/local.clash-dns-guard
temporary=$(mktemp /etc/pf.anchors/.clash-dns-guard.XXXXXX)
trap 'rm -f "$temporary"' EXIT
ifconfig -l | tr ' ' '\n' | render_rules > "$temporary"
pfctl -n -a "$anchor" -f "$temporary"
chmod 644 "$temporary"
mv "$temporary" "$rules"
pfctl -a "$anchor" -f "$rules"
token=/var/run/local.clash-dns-guard.token
if [ ! -s "$token" ]; then
  output=$(pfctl -E 2>&1)
  value=$(printf '%s\n' "$output" | awk '/Token/ {print $NF}')
  [ -n "$value" ]
  umask 077
  printf '%s\n' "$value" > "$token"
fi
```

### `local.clash-dns-guard.plist`

<!-- file: local.clash-dns-guard.plist -->
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>local.clash-dns-guard</string>
  <key>ProgramArguments</key><array><string>/usr/local/libexec/clash-dns-guard</string></array>
  <key>RunAtLoad</key><true/>
</dict></plist>
```

### `macos-dns-rollback.sh`

<!-- file: macos-dns-rollback.sh -->
```sh
#!/bin/sh
# First installation only: existing guards must use their own saved rollback.
set -eu
PATH=/usr/bin:/bin:/usr/sbin:/sbin
export PATH
[ "$(id -u)" -eq 0 ]
trial=/var/run/local.clash-dns-guard.trial
case "${1:-}" in
  --watch)
    sleep 120
    mkdir "$trial/decision" 2>/dev/null || exit 0
    ;;
  --rollback) ;;
  *) exit 2 ;;
esac
launchctl bootout system/local.clash-dns-guard 2>/dev/null || true
pfctl -a com.apple/000.clash-dns-guard -f /dev/null
token=/var/run/local.clash-dns-guard.token
if [ -s "$token" ]; then
  pfctl -X "$(cat "$token")"
  rm -f "$token"
fi
rm -f /usr/local/libexec/clash-dns-guard \
  /Library/LaunchDaemons/local.clash-dns-guard.plist \
  /etc/pf.anchors/local.clash-dns-guard
printf 'ROLLED_BACK\n' > "$trial/result"
```

## 仓库本地验证

`python3 tests/validate.py` 会提取并渲染本 README 的模板，检查凭据复用、参数替换、统计跨月、异常保留、超额显示、DNS 固定出口、规则顺序及物理接口过滤。它只操作临时目录，不连接 AWS、不创建资源。设置 `CADDY_BIN` 可额外执行本地 HTTP 与信号重载测试；设置 `MIHOMO_BIN` 和 `MIHOMO_DATA_DIR` 可执行核心配置校验和“节点断开且选择器 DIRECT 时 DNS 不回退”的隔离回归。PF 测试仅生成规则文本并以替身命令验证超时回退与已提交保留，不加载系统防火墙；HTTP 测试需要允许监听回环端口。测试通过仍需按第 10 节验证新部署。
