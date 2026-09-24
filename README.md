# PAF 论文网站（相对路径版）

## 打开与分享

双击本目录中的 `index.html`，即可离线浏览图片、视频和论文 PDF，无需启动服务器。

分享时请将整个 `html` 文件夹一起发送，保留以下相对位置。不要只发送 `index.html`。

- `index.html`：网站入口。
- `styles.css`、`main.js`、`favicon.svg`：样式、交互与图标。
- `media/`：H.264 摘要视频和预览图。
- `assets/images/`：论文图片。
- `assets/affordance/`：仿真及真机 affordance 视频和预览图。
- `assets/demos/`：两种光照条件下的真机演示与预览图。
- `assets/paper.pdf`：论文 PDF。

所有页面资源均使用本文件夹内的相对路径，没有对桌面、原始素材目录或上级目录的依赖。可将整个文件夹移动到任意位置。

## 可选的本地服务器

在此文件夹中运行：

```sh
python3 preview.py --port 8000
```

访问 http://localhost:8000/ 。该服务支持视频分段请求与进度拖动。

## 单文件版

`PAF-standalone.html` 是将素材内嵌的单文件版本，独立于上述相对路径网页。它不需要 `assets/`，但文件较大。

修改源网页后，可重新生成单文件版：

```sh
python3 build_standalone.py
```

生成 `PAF-standalone.html` 和 `PAF-standalone.zip`。常规目录版和单文件版选择一种分享即可。
