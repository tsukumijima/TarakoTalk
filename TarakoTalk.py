
import argparse
import chardet
import requests
import sys
from io import BufferedWriter
from pathlib import Path
from playsound import playsound
from rich.console import Console
from typing import TextIO


VERSION = '1.0.0'

def main():

    # Rich でログを出力するためのコンソールオブジェクト
    ## 標準出力と被らないように、標準エラー出力に出力
    console = Console(stderr=True)

    # 引数設定
    ## ref: https://sig9.org/archives/4478
    parser = argparse.ArgumentParser(
        formatter_class = argparse.RawTextHelpFormatter,
        description = 'Hiroyuki CLI TTS Application',
    )
    parser.add_argument('-v', '--version', action='version', help='バージョン情報を表示する', version=f'TarakoTalk version {VERSION}')
    subparsers = parser.add_subparsers()
    parser_save = subparsers.add_parser('save', help='生成した音声をファイルに保存する')
    parser_save.add_argument('input', help='ひろゆきに喋らせるテキスト (文字列 or ファイルパス、"-" で標準入力から読み込み)')
    parser_save.add_argument('output', help='生成した音声 (wav) の保存先のファイルパス ("-" で標準出力に出力)')
    parser_play = subparsers.add_parser('play', help='生成した音声を PC 上で再生する')
    parser_play.add_argument('input', help='ひろゆきに喋らせるテキスト (文字列 or ファイルパス、"-" で標準入力から読み込み)')

    # ひろゆきに喋らせるテキストを取得
    def GetTTSText(input_data: str) -> str:

        input_text: str = ''

        ## 標準入力から読み込み
        if input_data == '-':

            # stdin のデータをすべて読み込む
            input_text = sys.stdin.read()

        # ファイルから読み込み (ファイルが存在する場合のみ)
        elif Path(input_data).is_file():

            # 文字エンコーディングを自動判定して読み込み
            with open(input_data, 'rb') as f:
                input_text_raw = f.read()
            input_text_encoding = chardet.detect(input_text_raw)['encoding']
            input_data = input_text_raw.decode(input_text_encoding)

        # それ以外の場合、input_data に与えられたテキストをそのままひろゆきに喋らせる
        else:
            input_text = input_data

        return input_text

    # 保存時のハンドラー
    def SaveHandler(args):

        # ひろゆきに喋らせるテキストを取得
        input_text = GetTTSText(args.input)

        # 保存先のファイルのファイルオブジェクトを取得
        output_file_path: str = args.output
        output_file: BufferedWriter | TextIO

        ## 標準出力に出力
        if output_file_path == '-':
            output_file = sys.stdout

        ## ファイルに出力
        else:

            # ファイルではなくフォルダが指定された場合を弾く
            if Path(output_file_path).is_dir():
                console.print('[red]Error: 保存先のファイルパスが不正です。')
                console.rule(characters='─', align='center')
                sys.exit(1)

            # ファイルパス途中にあるフォルダをすべて作成 (すでにある場合は何もしない)
            Path(output_file_path).parent.mkdir(parents=True, exist_ok=True)

            # ファイルをバイナリ書き込みモードで開く
            try:
                output_file = open(output_file_path, 'wb')
            except Exception:
                console.print('[red]Error: 保存先のファイルを開けませんでした。')
                console.print_exception(width=100)
                console.rule(characters='─', align='center')
                sys.exit(1)

    # 再生時のハンドラー
    def PlayHandler(args):

        # ひろゆきに喋らせるテキストを取得
        input_text = GetTTSText(args.input)

    # サブコマンドのイベントを登録
    parser_save.set_defaults(handler=SaveHandler)
    parser_play.set_defaults(handler=PlayHandler)

    # 引数解析を実行
    args = parser.parse_args()
    if hasattr(args, 'handler'):
        console.rule(title=f'TarakoTalk (voiced by CoeFont) version {VERSION}', characters='─', align='center')
        args.handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
