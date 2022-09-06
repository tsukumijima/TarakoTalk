
import argparse
import atexit
import chardet
import requests
import simpleaudio
import sys
import tempfile
from pathlib import Path
from rich.console import Console
from rich.progress import Progress
from rich.progress import BarColumn, SpinnerColumn, TextColumn, TimeElapsedColumn
from typing import IO


VERSION = '1.0.0'

def main():

    # Rich でログを出力するためのコンソールオブジェクト
    ## 標準出力と被らないように、標準エラー出力に出力
    console = Console(stderr=True)

    # 引数設定
    ## ref: https://sig9.org/archives/4478
    parser = argparse.ArgumentParser(
        formatter_class = argparse.RawTextHelpFormatter,
        description = 'Cross-platform CLI TTS Application for Hiroyuki\'s Voice',
    )
    subparsers = parser.add_subparsers()
    parser_save = subparsers.add_parser('save', help='生成した音声をファイルに保存する')
    parser_save.add_argument('input', help='ひろゆきに喋らせるテキスト (文字列 or ファイルパス、"-" で標準入力から読み込み)')
    parser_save.add_argument('output', help='生成した音声ファイル (wav) の保存先のファイルパス ("-" で標準出力に出力)')
    parser_play = subparsers.add_parser('play', help='生成した音声を PC 上で再生する')
    parser_play.add_argument('input', help='ひろゆきに喋らせるテキスト (文字列 or ファイルパス、"-" で標準入力から読み込み)')


    # プログレスバーの設定
    def CreateProgressBar() -> Progress:
        return Progress(
            SpinnerColumn(spinner_name='bouncingBar'),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=9999),  # とりあえず適当に大きい幅に設定しておく
            TimeElapsedColumn(),
            console = console,
            transient = False,
            expand = True,  # ターミナルの幅いっぱいに表示
        )


    def GetTTSText(input_data: str) -> str:
        """
        ひろゆきに喋らせるテキストを取得する

        Args:
            input_data (str): input 引数

        Returns:
            str: ひろゆきに喋らせるテキスト
        """

        input_text: str = ''

        ## 標準入力から読み込み
        if input_data == '-':

            # stdin のデータをすべて読み込む
            # 文字エンコーディングを自動判定して読み込み
            input_text_raw = sys.stdin.buffer.read()
            input_text_encoding = chardet.detect(input_text_raw)['encoding']
            input_text = input_text_raw.decode(input_text_encoding)

        # ファイルから読み込み (ファイルが存在する場合のみ)
        elif Path(input_data).is_file():

            # 文字エンコーディングを自動判定して読み込み
            with open(input_data, mode='rb') as f:
                input_text_raw = f.read()
            input_text_encoding = chardet.detect(input_text_raw)['encoding']
            input_text = input_text_raw.decode(input_text_encoding)

        # それ以外の場合、input_data に与えられたテキストをそのままひろゆきに喋らせる
        else:
            input_text = input_data

        # 改行やホワイトスペースを消した上で返す
        return input_text.strip()


    def TextToSpeech(input_text: str, output_file: IO[bytes]) -> bool:
        """
        Text-To-Speech を実行し、生成した音声をファイルに保存する

        Args:
            input_text (str): ひろゆきに喋らせるテキスト
            output_file (IO[bytes]): 保存先のファイルの file-like オブジェクト

        Returns:
            bool: Text-To-Speech の実行に成功したか
        """

        # API に渡すヘッダー
        headers ={
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'ja,ja-JP;q=0.9,und;q=0.8',
            'origin': 'https://hiroyuki.coefont.cloud',
            'referer': 'https://hiroyuki.coefont.cloud/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36',
        }

        console.print(f'📋 テキスト: {input_text}')

        # 処理が終わるまでプログレスバーを表示
        with CreateProgressBar() as progress:

            # プログレスバー (終了未定) を表示
            progress.add_task('音声を生成しています…', total=None)

            # Text-To-Speech を実行
            result = requests.post(
                url = 'https://tgeedx93af.execute-api.ap-northeast-1.amazonaws.com/production/hiroyuki/text2speech',
                headers = headers,
                json = {
                    'coefont': '19d55439-312d-4a1d-a27b-28f0f31bedc5',  # ひろゆきの CoeFont 固定
                    'text': input_text,
                },
            )

        # HTTP ステータスコードが 200 で音声の生成に成功している場合のみ
        if result.status_code == 200 and result.json()['statusCode'] == 200 and result.json()['body']['success'] is True:

            # 生成された音声のキーを取得
            wav_key: str = result.json()['body']['wav_key']

            # 処理が終わるまでプログレスバーを表示
            with CreateProgressBar() as progress:

                # プログレスバー (終了未定) を表示
                progress.add_task('生成した音声をダウンロードしています…', total=None)

                # 生成された音声をダウンロード
                wav_result = requests.get(
                    url = f'https://tgeedx93af.execute-api.ap-northeast-1.amazonaws.com/production/chore/get_presigned_url?wav_key={wav_key}',
                    headers = headers,
                )

            # ダウンロードに成功
            if wav_result.status_code == 200:

                # ダウンロードしたデータをファイルに書き込む
                output_file.write(wav_result.content)
                return True

            # ダウンロードに失敗した
            else:
                console.print('[red]❌ 生成した音声のダウンロードに失敗しました。CoeFont のサーバーが混雑している可能性があります。\n'
                              f'   (HTTP Error {wav_result.status_code})')
                return False

        # 音声の生成に失敗した
        else:

            # ステータスコードが 200 以外
            if result.status_code != 200:
                console.print('[red]❌ 音声の生成に失敗しました。CoeFont のサーバーが混雑している可能性があります。\n'
                              f'   (HTTP Error {result.status_code})')

            # テキストに NG ワードが含まれている
            elif result.json()['statusCode'] != 200 and 'ng_word' in result.json()['body']:
                console.print(
                    f'[red]❌ NGワード「{result.json()["body"]["ng_word"]}」が含まれているため、音声の生成に失敗しました。\n'
                    '   テキストを変更して再度お試しください。'
                )

            # それ以外の理由で音声の生成に失敗した
            else:
                console.print(
                    '[red]❌ 音声の生成に失敗しました。CoeFont のサーバーが混雑している可能性があります。\n'
                    f'   (HTTP Error {result.json()["body"]["statusCode"]} / Message: {result.json()["body"]["error"]["message"]})'
                )

            return False


    # 保存時のハンドラー
    def SaveHandler(args):

        # ひろゆきに喋らせるテキストを取得
        input_text = GetTTSText(args.input)

        # 保存先のファイルの file-like オブジェクトを取得
        output_file_path: str = args.output
        output_file: IO

        ## 標準出力に出力
        is_stdout = False
        if output_file_path == '-':
            output_file = sys.stdout.buffer  # sys.stdout.buffer から BinaryIO が取れる
            is_stdout = True

        ## ファイルに保存
        else:

            # ファイルではなくフォルダが指定された場合を弾く
            if Path(output_file_path).is_dir():
                console.print('[red]❌ 保存先のファイルパスが不正です。')
                sys.exit(1)

            # ファイルパス途中にあるフォルダをすべて作成 (すでにある場合は何もしない)
            Path(output_file_path).parent.mkdir(parents=True, exist_ok=True)

            # ファイルをバイナリ書き込みモードで開く
            try:
                output_file = open(output_file_path, mode='wb')
            except Exception:
                console.print('[red]❌ 保存先のファイルを開けませんでした。')
                console.print_exception(width=100)
                sys.exit(1)

        # Text-To-Speech を実行し、ファイルに保存
        result = TextToSpeech(input_text, output_file)

        # ファイルを閉じる (重要)
        output_file.close()

        # 実行に失敗した場合はここで終了
        if result is False:
            if is_stdout is False:
                Path(output_file_path).unlink()
            sys.exit(1)

        console.print(f'✅ 生成した音声を{"標準出力" if is_stdout else f" {Path(output_file_path).absolute()} "}に保存しました。')


    # 再生時のハンドラー
    def PlayHandler(args):

        # ひろゆきに喋らせるテキストを取得
        input_text = GetTTSText(args.input)

        # 一時保存先の一時ファイルを開く
        output_temp_file = tempfile.NamedTemporaryFile(mode='wb', delete=False)

        # Text-To-Speech を実行し、一時ファイルに保存
        result = TextToSpeech(input_text, output_temp_file)

        # 一時ファイルを閉じる (まだ削除はされない)
        output_temp_file.close()

        # 実行に失敗した場合はここで終了
        if result is False:
            Path(output_temp_file.name).unlink()  # 一時ファイルを削除
            sys.exit(1)

        # 処理が終わるまでプログレスバーを表示
        with CreateProgressBar() as progress:

            # プログレスバー (終了未定) を表示
            progress.add_task('生成した音声を再生しています…', total=None)

            # 生成された音声を再生 (再生し終わるまでブロッキングされる)
            # ref: https://laboratory.kazuuu.net/play-an-mp3-file-in-python-using-playsound/
            play_object = simpleaudio.WaveObject.from_wave_file(output_temp_file.name).play()
            play_object.wait_done()
            console.print('✅ 生成した音声を再生しました。')

            Path(output_temp_file.name).unlink()  # 一時ファイルを削除


    # サブコマンドのイベントを登録
    parser_save.set_defaults(handler=SaveHandler)
    parser_play.set_defaults(handler=PlayHandler)

    # 終了時にラインを表示し、標準入出力を閉じる
    def OnExit():
        console.rule(characters='─', align='center')
        sys.stdin.close()
        sys.stdout.close()
        sys.stderr.close()
    atexit.register(OnExit)

    # 引数解析を実行
    console.rule(title=f'TarakoTalk (Voiced by CoeFont) version {VERSION}', characters='─', align='center')
    args = parser.parse_args()
    if hasattr(args, 'handler'):
        args.handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
