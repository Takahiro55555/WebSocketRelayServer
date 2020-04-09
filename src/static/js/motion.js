//参考URL: https://tknc.jp/tp_detail.php?id=1116
let isGyro = false;
const gyroUpdateIntervalSec = 1;
let gyroBeforeUpdate = 0;
let isAvailableWebsocket = false;
let ws;
let wsUrl = null;
let relayIdPublic = null;

if( getParam('protocol') != null && getParam('relayId') != null) {
    wsUrl = getParam('protocol') + '://' + location.host + '/ws/v1/relays/' + getParam('relayId');
    relayIdPublic = getParam('relayId').match(/^[0-9a-zA-Z]+/)[0];
    document.getElementById('ws-url').innerText = wsUrl;
}else{
    document.getElementById('ws-url').innerText = 'Invalid URL Parameter!!!';
}

if ( localStorage.getItem(relayIdPublic) ){
    makeToReconnectButton(document.getElementById('connect'));
} else {
    makeToConnectButton(document.getElementById('connect'));
}

document.getElementById('connect').addEventListener('click', function () {
    if(wsUrl == null){
        errorPrintln('[Parameter] 無効なURLパラメータです。');
        return;
    }

    if (isAvailableWebsocket) {
        isAvailableWebsocket = false;
        let msg = {
            "header":{
                "cmd": "exit"
            },
            "contents": null
        }
        ws.send(JSON.stringify(msg));
        localStorage.removeItem(relayIdPublic);
        makeToConnectButton(document.getElementById('connect'));
        return;
    }

    logPrintln("[WebSocket] Connecting to: " + wsUrl);
    try {
        ws = new WebSocket(wsUrl);
    } catch (e) {
        errorPrintln("[WebSocker] 接続に失敗しました");
        return;
    }

    ws.onopen = function (e) {
        logPrintln("[WebSocket] 接続に成功しました");
        isAvailableWebsocket = true;
        makeToDisconnectButton(document.getElementById('connect'));
        let clientId = localStorage.getItem(relayIdPublic);
        let msg = {
            "header":{
                "cmd": "connect",
                "client_id": clientId
            },
            "contents": null
        };
        if ( clientId ) {
            // 再接続
            msg['header']['cmd'] = 'reconnect';
            logPrintln('[WebSocket] reconnect');
            logPrintln(JSON.stringify(msg));
        }
        ws.send(JSON.stringify(msg));
    }

    ws.onmessage = function(e) {
        let msg = JSON.parse(e.data);
        if ( msg.errors ){
            errorPrintln('[WebSocket][Message] ' + String(e.data));
        } else {
            logPrintln('[WebSocket][Message] ' + String(e.data));
        }
        if ( msg.header.client_id ){
            localStorage.setItem(relayIdPublic, msg.header.client_id);
            logPrintln('[WebSocket] Save new client id: ' + msg.header.client_id);
        }
    }

    ws.onerror = function (error) {
        errorPrintln("[WebSocker] エラーが発生しました");
        isAvailableWebsocket = false;
        if ( localStorage.getItem(relayIdPublic) ){
            makeToReconnectButton(document.getElementById('connect'));
        } else {
            makeToConnectButton(document.getElementById('connect'));
        }
    }

    ws.onclose = function (e) {
        logPrintln("[WebSocket] 接続が切断されました");
        logPrintln("[WebSocket] Code: " + String(e.code));
        logPrintln("[WebSocket] Reason: " + e.reason);
        isAvailableWebsocket = false;
        
        if ( localStorage.getItem(relayIdPublic) ){
            makeToReconnectButton(document.getElementById('connect'));
        } else {
            makeToConnectButton(document.getElementById('connect'));
        }
    }
})


if ((window.DeviceOrientationEvent) && ('ontouchstart' in window)) {
    isGyro = true;
    logPrintln("ジャイロセンサーを搭載しています");
}

//PCなど非ジャイロ
if (!isGyro) {
    // ここに何か関数
    errorPrintln("ジャイロセンサーを搭載していません");
    //一応ジャイロ持ちデバイス
} else {
    //ジャイロ動作確認
    let resGyro = false;
    window.addEventListener("deviceorientation", doGyro, false);
    function doGyro() {
        resGyro = true;
        window.removeEventListener("deviceorientation", doGyro, false);
        gyroIsAllowed();

        //参考URL: https://kkblab.com/make/javascript/gyro.html
        // ジャイロセンサの値が変化したら実行される deviceorientation イベント
        window.addEventListener("deviceorientation", (dat) => {
            if (performance.now() - gyroBeforeUpdate < gyroUpdateIntervalSec * 1000) {
                return;
            }
            gyroBeforeUpdate = performance.now();
            alpha = dat.alpha;  // z軸（表裏）まわりの回転の角度（反時計回りがプラス）
            beta = dat.beta;   // x軸（左右）まわりの回転の角度（引き起こすとプラス）
            gamma = dat.gamma;  // y軸（上下）まわりの回転の角度（右に傾けるとプラス）
            logPrintln("a: " + alpha + ", b: " + beta + ", g: " + gamma);
            msg = {
                'header': {
                    'cmd': 'relay'
                },
                'contents': {
                    'gyro':{
                        alpha,
                        beta,
                        gamma
                    }
                }
            }
            if (isAvailableWebsocket) {
                ws.send(JSON.stringify(msg));
            }
        });
    }

    //数秒後に判定
    setTimeout(function () {
        //ジャイロが動いた
        if (resGyro) {
            // ここに何か関数
            gyroIsAllowed();

            //ジャイロ持ってるくせに動かなかった
        } else {
            gyroIsNotAllowed();
            //iOS13+方式ならクリックイベントを要求
            if (typeof DeviceOrientationEvent.requestPermission === "function") {
                //ユーザアクションを得るための要素を表示
                logPrintln("iOS13+方式です");
                const body = document.getElementById("body");
                body.onclick = function () {
                    logPrintln("クリックされました");
                    DeviceOrientationEvent.requestPermission().then(res => {
                        logPrintln("許可を確認ダイアログが出現するはずです...");
                        //「動作と方向」が許可された
                        if (res === "granted") {
                            // ここに何か関数
                            gyroIsAllowed();
                            logPrintln("動作と方向が許可されました");
                            //「動作と方向」が許可されなかった
                        } else {
                            isGyro = false;
                            // ここに何か関数
                            gyroIsNotAllowed();
                            logPrintln("動作と方向が許可されませんでした");
                        }
                    });
                };

                //iOS13+じゃない
            } else {
                //早くアップデートしてもらうのを祈りながら諦める
                isGyro = false;
                // ここに何か関数
                logPrintln("早くアップデートしてもらうのを祈りながら諦める");
            }
            gyroIsNotAllowed();
        }
    }, 300);
}

function gyroIsAllowed() {
    msg = "[OK]ジャイロセンサーを利用することが可能になりました";
    logPrintln(msg);
}

function gyroIsNotAllowed() {
    msg = "ジャイロセンサーを利用できません";
    errorPrintln(msg);
}

function makeToConnectButton(buttonElement){
    buttonElement.innerText = '接続';
    buttonElement.classList.add('btn-primary');
    buttonElement.classList.remove('btn-danger');
    buttonElement.classList.remove('btn-success');
}

function makeToDisconnectButton(buttonElement){
    buttonElement.innerText = '切断';
    buttonElement.classList.add('btn-danger');
    buttonElement.classList.remove('btn-primary');
    buttonElement.classList.remove('btn-success');
}

function makeToReconnectButton(buttonElement){
    buttonElement.innerText = '再接続';
    buttonElement.classList.add('btn-success');
    buttonElement.classList.remove('btn-primary');
    buttonElement.classList.remove('btn-danger');
}

/**
 * エラーメッセージをhtmlのコンソールエレメントの先頭（1行目）に表示する
 * "error"クラスを適用
 * @param {表示したいメッセージ} msg 
 */
function errorPrintln(msg) {
    const newLogElement = document.createElement("div");
    newLogElement.textContent = "[Error] " + msg;
    newLogElement.className = "error";
    htmlConsolePrintln(newLogElement);
    console.log(msg);
}

/**
 * ログメッセージをhtmlのコンソールエレメントの先頭（1行目）に表示する
 * "log"クラスを適用
 * @param {表示したいメッセージ} msg 
 */
function logPrintln(msg) {
    const newLogElement = document.createElement("div");
    newLogElement.textContent = "[Log] " + msg;
    newLogElement.className = "log";
    htmlConsolePrintln(newLogElement);
    console.log(msg);
}

/**
 * htmlのコンソールエレメントの先頭（1行目）に当該エレメントを追記する
 * @param {htmlのエレメント} element 
 */
function htmlConsolePrintln(element) {
    if (!element) return;
    const consoleElement = document.getElementById("console");
    consoleElement.insertAdjacentElement('beforeend', element);
    let bottom = consoleElement.scrollHeight - consoleElement.clientHeight;
    consoleElement.scroll(0, bottom);
}


/**
 * Get the URL parameter value
 * Ref: https://stackoverflow.com/questions/901115/how-can-i-get-query-string-values-in-javascript
 * @param  name {string} パラメータのキー文字列
 * @return  url {url} 対象のURL文字列（任意）
 */
function getParam(name, url) {
    if (!url) url = window.location.href;
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, " "));
}