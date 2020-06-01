# WebSocketRelayServer

※）電気通信事業法の適用がある「他人の通信を媒介」するサービスとなってしまうため、本システムは一般公開しておりません。

## これは何？
WebSocketのデータを中継するためのWebサーバです。
PythonのWebフレームワークである
[Tornado](https://www.tornadoweb.org/en/stable/)
を使用しています。

また、トークンや認証情報（メールアドレス、ハッシュ化したパスワード）を保存するためのDBにはSQLiteを、ORMには
[SQLAlchemy](https://www.sqlalchemy.org/)
を使用しています。

バーチャルホストとHTTPSに対応させるために、
[jwilder/nginx-proxy](https://hub.docker.com/r/jwilder/nginx-proxy)
というDockerイメージと
[jrcs/letsencrypt-nginx-proxy-companion](https://hub.docker.com/r/jrcs/letsencrypt-nginx-proxy-companion)
というDockerイメージを使用し、公開しました。

## なぜ作った!?
スマートフォンのブラウザから、ジャイロセンサーの値をRaspberry Piへ送信し、スマートフォンの傾きとRaspberryPiのカメラの傾きを連動させようと考えたのがきっかけです。

[AWS IoT](https://docs.aws.amazon.com/ja_jp/iot/latest/developerguide/what-is-aws-iot.html)
や
[Pusher](https://pusher.com/)
を使用しなかったのは、ただ単にこのようなシステムを作って見たかったからです。

## 構成
- 端末：iPhone7
- 制御ボード：Raspberry Pi 4
- Google Compute Engine f1-micro（vCPU x 1、メモリ 0.6 GB）
- サーバゾーン：us-east
- 端末地域：日本
- 動画配信：[WebRTC Native Client Momo](https://github.com/shiguredo/momo)

## 動作の様子
以下の動画は、実際に使用した際の動画です。クリックすることで見ることができます（Twitter）。
[![thumbnail](https://pbs.twimg.com/ext_tw_video_thumb/1254172958227968001/pu/img/LrT2jVR-osK-lPls.jpg)](https://twitter.com/i/status/1254174635333058560)
