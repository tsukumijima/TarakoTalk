
# TarakoTalk

![screenshot](https://user-images.githubusercontent.com/39271166/188684161-f4766df8-797d-4091-bf6e-3176db94e073.png)

[おしゃべりひろゆきメーカー](https://hiroyuki.coefont.cloud/) を使って CLI からひろゆきに適当な事を喋らせられる、非公式な CLI TTS (Text-to-Speech) ツールです。

## Features

生成した音声をファイルに保存する `save` と、生成した音声をそのまま PC で再生する `play` の2つのサブコマンドを実装しています。

140 文字までの制限がある Web サイトとは異なり、TarakoTalk は 1000 文字までのテキストをひろゆきに喋らせられます (2022/09/06 時点での API の仕様に基づく)。  
コピペや短い物語をひろゆきに朗読させることもできます。  
音声の生成には、短いものだと5秒、最大で15秒ほど時間がかかるようです（サーバーの混雑時はもっとかも）。

- **生成した音声をファイルに保存する (`save`)**
  - 喋らせたいテキストは、コマンドライン引数・テキストファイル・標準入力（パイプ渡し）のいずれかから入力可能
  - 生成した音声を、指定したファイルパスに wav 形式で保存
  - 生成した音声を、wav 形式で標準出力（パイプ渡し）に出力
    - 別途 FFmpeg を導入すれば、`tarakotalk save "それって、あなたの感想ですよね？" "-" | ffmpeg -i - test.mp3` で wav から mp3 などの音声フォーマットに変換できます。
- **生成した音声を PC 上で再生する (`play`)**
  - 喋らせたいテキストは、コマンドライン引数・テキストファイル・標準入力（パイプ渡し）のいずれかから入力可能
  - 生成した音声を、そのまま PC のスピーカーから再生 (クロスプラットフォーム対応)

## How to Use

[Releases](https://github.com/tsukumijima/TarakoTalk/releases) から最新の TarakoTalk をダウンロードして、適宜 PATH の通ったフォルダに配置します。  

> TarakoTalk は Python 製のツールですが、[Nuitka](https://github.com/Nuitka/Nuitka) を使い単一のバイナリにビルドしています。

- Windows (x64): TarakoTalk.exe
- macOS (x64): tarakotalk-macos
  - Intel Mac 版のみですが、Apple Silicon (M1) Mac でも Rosetta 2 が入っていれば動くはず…？
- Linux (x64): tarakotalk-linux
- Linux (arm64): tarakotalk-linux-arm

上記の4つのビルドがあります。お使いの OS に合わせてダウンロードしてください。

```
usage: ./tarakotalk [-h] {save,play} ...

Cross-platform CLI TTS Tools for Hiroyuki's Voice

positional arguments:
  {save,play}
    save       生成した音声をファイルに保存する
    play       生成した音声を PC 上で再生する

options:
  -h, --help   show this help message and exit
```

### `tarakotalk save`

```
usage: ./tarakotalk save [-h] input output

positional arguments:
  input       ひろゆきに喋らせるテキスト (文字列 or ファイルパス、"-" で標準入力から読み込み)
  output      生成した音声ファイル (wav) の保存先のファイルパス ("-" で標準出力に出力)

options:
  -h, --help  show this help message and exit
```

```powershell
# コマンドライン引数からテキストを入力し、生成した音声を /path/to/test.wav に保存
./tarakotalk save "それって、あなたの感想ですよね？" "/path/to/test.wav"

# ファイルからテキストを入力し、生成した音声を標準出力に出力したあと、FFmpeg に渡して mp3 に変換
./tarakotalk save "/path/to/yoshinoya.txt" "-" | ffmpeg -i - -c:a libmp3lame /path/to/test.mp3

# 標準入力からテキストを読み上げ、生成した音声を /path/to/test.wav に保存
echo "それって、あなたの感想ですよね？" | ./tarakotalk save "-" "/path/to/test.wav"
```

### `tarakotalk play`

```
usage: ./tarakotalk play [-h] input

positional arguments:
  input       ひろゆきに喋らせるテキスト (文字列 or ファイルパス、"-" で標準入力から読み込み)

options:
  -h, --help  show this help message and exit
```

```powershell
# コマンドライン引数からテキストを読み上げ
./tarakotalk play "それって、あなたの感想ですよね？"

# ファイルからテキストを読み上げ
./tarakotalk play "/path/to/yoshinoya.txt"

# 標準入力からテキストを読み上げ
echo "それって、あなたの感想ですよね？" | ./tarakotalk play "-"
```

## Examples of Use

とりあえず使えそう (要出典) な例を適当に挙げてみただけで、実際に使えるかどうかは未検証です。

- [吉野家コピペ](https://dic.nicovideo.jp/a/%E5%90%89%E9%87%8E%E5%AE%B6%E3%82%B3%E3%83%94%E3%83%9A) をひろゆきに朗読させる
- [棒読みちゃん](https://chi.usamimi.info/Program/Application/BouyomiChan/) みたいにライブチャットのコメントを読み上げさせる
  - 別途、ライブチャットからコメントを受信した際に、コメント内容とともにコマンドを実行できるツールが必要です。そんなものがあるのかは知らん。
  - 音声の生成には短いコメントでも数秒時間がかかるので、どうしてもリアルタイム性は落ちます。
- ラズパイに TarakoTalk をインストールして、ラズパイにつなげたスピーカーから朝8時になったタイミングで今日の天気とニュースをひろゆきに読み上げさせる
  - 生成は（当然ながら）CoeFont のサーバーに丸投げしているので、ラズパイのような非力なマシンでもそれなりに早く生成できるはずです。
    - 生成した音声は標準出力に流せるので、FFmpeg でパイプ渡しされてきた標準入力を受け取るようにすれば (`-i -`)、FFmpeg のコマンド次第で別の音声形式に変換したり、再生速度を変更することもできます。
    - FFmpeg を活用して、読み上げ音声に BGM を入れたりフィルタを掛けたりとかもできそう。
- ひろゆきに読み上げさせたものをナレーションとして動画に使う
  - 動画作成に使うなら、公式で [CoeFont Cloud](https://coefont.cloud/) 内の無料無制限で使える CoeFont にひろゆきが入っているので、そっちを使ったほうがイントネーションやスピードの再生もできてより便利だと思います（なぜかあまり宣伝されていない…）。
    - CoeFont Cloud の利用にはログインが必要です。
    - CoeFont は有料のものもありますが、ひろゆきはアリアル・ミリアルに続いての無料枠扱いみたいです。落差が激しい…
- 音MAD素材用に原曲の歌詞をひろゆきに流し込んで、別途 REAPER か VocalShifter あたりで調教して歌わせる
  - CLI ツールなので、シェルスクリプトか何かを組んで歌詞の読み上げ音声を複数の wav ファイルに分割して生成させるようにすることもできそうです。

## Disclaimer

- **<u>TarakoTalk は非公式ツールです。CoeFont 公式とは一切関係がありません。</u>**
  - TarakoTalk は、おしゃべりひろゆきメーカーが内部的に使っている非公開 API に直接アクセスすることで、CLI からひろゆきの音声を取得しています。
  - TarakoTalk に関して CoeFont 公式に問い合わせるのはやめてください。
- **<u>無保証です。</u>CoeFont 公式やひろゆき本人から怒られが発生しない程度に<s>こっそり</s>使ってください。**
  - **万が一、どこからか怒られが発生した場合の責任は一切負いかねます。** 自己の責任のもとで使ってください。
  - 非公開 API にアクセスしている時点で元々好ましいことをしているツールではないので、CoeFont のサーバーに過剰に負荷がかかるような使い方はやめてあげてください。
  - NG ワードは API 側でバリデーションされているため、TarakoTalk 経由かどうかにかかわらず、NG ワードには同じものが適用されます。
  - CoeFont 側の API の仕様変更、あるいはサービス終了などに伴って、急に使えなくなる可能性があります。

## License

[MIT License](License.txt)
