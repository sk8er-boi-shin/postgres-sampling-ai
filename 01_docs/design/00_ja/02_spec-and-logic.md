# 目次
 
1. [入出力仕様](#1入出力仕様)  
2. [モジュール構成](#2モジュール構成)  
3. [考慮すべきデータ構造と仕様](#3考慮すべきデータ構造と仕様)  
4. [外部インターフェース（DB/API等）](#4外部インターフェースdbapi等)  
5. [AIによるサンプリング行数の推定ロジック](#5aiによるサンプリング行数の推定ロジック)  
6. [エラーハンドリング・ロギング](#6エラーハンドリング・ロギング)  

📘 **本ドキュメントで使用する用語や技術的な前提知識については、[参考資料・用語集](./03_reference.md#前提知識) を参照してください。**

---
# 1.入出力仕様

本章では、ツールの主な入出力対象を示す。対象はCLIツールとしての実行に基づき、設定ファイル、DB接続情報、AI推定処理の入出力、ログ等を含む。


### 入力仕様

| 区分 | 内容 | 形式・例 | 備考 |
|------|------|-----------|------|
| クエリ指定 | 対象となるSQLクエリ（学習／適用フェーズ共通） | `SELECT * FROM sales WHERE amount > 1000;` | 設定ファイル or スクリプト内で指定（柔軟に変更可能）※1 |
| 対象DB情報 | DB接続情報（host, port, user, dbname等） | JSON または .env | セキュリティ上、平文保存禁止を推奨 |
| サンプリング条件 | サンプリング対象となるテーブルの設定 | YAML/JSON形式 | 除外スキーマや閾値含む |
| 学習済みモデル | 適用フェーズにおけるモデルファイル | `best_model.pkl` | 学習フェーズ後に生成されたファイル |
| 統計情報メトリクス | PostgreSQLシステムカタログから取得 | `pg_stat_all_tables`, `pg_stats`等 | 自動取得されるため、事前指定不要 |
| 実行モード | 処理の適用方法を制御するモード（通常実行など） | `--mode run` | dry-run的な挙動も将来的に視野に入れる。※2 |


※1：実行時の再現性・精度を担保するため、クエリの指定方法は状況に応じて柔軟に選択可能とする。  
　環境要因による影響を考慮しており、詳細な実行条件や構成は本設計書では割愛する。

※2：現時点では処理適用の有無をPythonロジック側で制御する方式に限定されており、  
　統計情報の更新を完全に抑止する dry-run 機能は一部制約がある。  
　今後、実行計画取得のみに限定したモードや、更新対象のログ出力のみを行う機能も検討中。



### 出力仕様

| 区分 | 内容 | 形式・例 | 備考 |
|------|------|-----------|------|
| 実行ログ | 処理結果や推定行数などを含むログ | `execution_20240624.log` | ログローテーション・圧縮対応を検討 |
| 推定結果 | テーブルごとの推定サンプリング行数 | CSV or JSON | `table_name,estimated_rows` 形式 |
| 統計更新結果 | ANALYZE 実行の成功／失敗、実行時間など | JSON or ログ内埋込 | `{"status":"success","time":2.13}` |
| 実行計画・統計履歴 | 実行クエリに対する EXPLAIN 結果など | 保存先：CSV or DBテーブル | モデル学習に再利用される |
| エラー出力 | 処理中のエラー情報 | stderr またはログファイル | リトライ対象か否かを判定するフラグ含む |
| モデルファイル | 学習済み回帰モデルなど | `best_model.pkl` | scikit-learn joblib / pickle形式想定 |


### 備考

- 入出力ファイルの形式はすべてUTF-8で統一
- モデルファイルや統計結果の出力先は `config.yaml` または CLI で変更可能
- クラウド連携（S3等）を行う場合、出力先URIに `s3://` 指定なども対応可能（拡張予定）

---

# 2.モジュール構成

本章では、本ツールにおける主要な処理フェーズ（学習フェーズ／適用フェーズ）を支えるモジュール構成について説明する。  
各モジュールは役割ごとに明確に分離されており、将来的な機能拡張や差し替えが容易な構造を目指す。


### 学習フェーズ（PoC・開発環境）

| モジュール名 | 役割 |
|--------------|------|
| `metrics_collector.py` | クエリに含まれるテーブルの統計情報（pg_stat系、pg_class等）を収集 |
| `sampling_estimator.py` | 統計情報をもとに、サンプリング行数をAI（回帰モデル）で推定 |
| `analyze_executor.py` | 推定値をもとにANALYZEを実行し、統計情報を更新 |
| `plan_logger.py` | クエリ実行後に実行計画と処理時間を取得・記録 |
| `model_trainer.py` | 実行結果をもとに回帰モデルを学習し、モデルファイル（.pkl）として保存 |



### 適用フェーズ（本番または運用想定）

| モジュール名 | 役割 |
|--------------|------|
| `metrics_collector.py` | 学習フェーズと同様にメトリクスを収集 |
| `model_loader.py` | 学習済みのモデルファイルを読み込み、推定処理に利用 |
| `analyze_executor.py` | 推定されたサンプリング行数でANALYZEを実行（dry-runモードも視野） |



### 共通・補助モジュール

| モジュール名 | 役割 |
|--------------|------|
| `logger.py` | 実行結果、異常系、推定結果のログ出力を担う共通ログ処理 |
| `config_loader.py` | 設定ファイル（YAML/JSON形式）の読み込みと共通パラメータ管理 |
| `query_parser.py` | 渡されたクエリからテーブルを抽出し、対象候補を整理 |
| `error_handler.py` | リトライ・スキップ・通知などのエラーハンドリング処理 |
| `constants.py` | しきい値・固定値などの定義と一元管理 |



### 拡張予定（将来的な構想）

| モジュール名（仮） | 役割 |
|------------------|------|
| `api_server.py` | Web UIや外部ツールからの呼び出しを受け付けるREST APIサーバ |
| `ui_adapter.py` | モデル結果や統計情報を可視化するUI出力変換処理 |
| `job_scheduler.py` | 定期実行や依存ジョブ管理を行うスケジューラ連携モジュール（cron/CI/CD対応） |



※ 各モジュールの責務は詳細設計フェーズにて更に細分化・明確化される予定。  
※ Pythonのパッケージ構成（例：`/modules/`, `/utils/` 等のディレクトリ設計）や依存関係の詳細は、製造・詳細設計フェーズにて整理・調整を行う予定。


---

# 3.考慮すべきデータ構造と仕様

本章では、統計情報の収集・推定・適用において考慮すべきPostgreSQLの内部構造やカラム特性、およびAIによる行数推定に必要となるデータ仕様について整理する。


### 1. PostgreSQLの統計情報関連構造

| テーブル／ビュー | 説明 | 主に使用するカラム例 |
|------------------|------|----------------------|
| `pg_class` | テーブルの基本情報 | `reltuples`, `relpages`, `relkind` |
| `pg_stat_all_tables` | テーブルごとの統計情報 | `n_tup_ins`, `n_tup_upd`, `n_tup_del`, `n_live_tup`, `n_dead_tup` |
| `pg_stat_user_indexes` | インデックス統計 | `idx_scan`, `idx_tup_read` |
| `pg_attribute` | 各カラムの定義 | `attname`, `attnum`, `attstattarget` |
| `pg_stats` | 列ごとの統計情報（プレーンビュー） | `null_frac`, `n_distinct`, `most_common_vals`, `histogram_bounds`, `correlation` |



### 2. AIモデル学習における特徴量（特徴ベクトル）

AIがサンプリング行数を推定するためには、以下のような特徴量を使用することを想定している：

- テーブルサイズに関する指標
  - `reltuples`（想定行数）
  - `relpages`（データサイズ）

- カラムの統計特性
  - `n_distinct`（ユニーク度）
  - `correlation`（並びの相関）
  - `null_frac`（NULL率）
  - 列数（特徴量の次元数としても活用）

- 更新頻度やデータの変動性
  - `n_tup_upd`, `n_tup_ins`, `n_tup_del`
  - `n_dead_tup`（断片化の度合い）

- その他のメタ情報（設計段階）
  - パーティションテーブルの有無
  - 部分インデックスの有無
  - スキーマ名、テーブル名の命名規則（除外判定用）


### 3. 考慮すべき仕様・制約事項

| 項目 | 説明 | 補足 |
|------|------|------|
| 外部テーブルの扱い | `pg_class.relkind = 'f'` のテーブルは対象外 | FDW経由のテーブルはANALYZE非対応 |
| パーティション構造 | 親子テーブルの関係によってANALYZE対象が異なる | `ANALYZE parent_table` で子が対象になるかどうかに注意 |
| 統計情報の更新粒度 | PostgreSQLは列単位で統計情報を管理 | `default_statistics_target` により調整可能 |
| extended statistics | PostgreSQL 10以降の複数列統計 | 現状では対象外だが、将来的に考慮する可能性あり |
| reltuplesの精度 | 実際の件数とズレが生じる場合あり | ANALYZE後でなければ信頼性が低いケースもある |
| pg_stat_xxx の遅延 | バッファキャッシュの反映遅延に注意 | 特に直後の更新・取得で差が出る可能性あり |
| INHERITS テーブル | PostgreSQL の旧式継承構造（INHERITS）は対象外 | 実運用では推奨されず、パーティションと誤認されるリスクあり |

---

### 4. 今後の拡張に備えたデータ構造想定

- 実行履歴ログ用の構造（CSV または DBテーブル）
  - `query_id`, `table_name`, `estimated_rows`, `actual_duration`, `plan_type`, `timestamp`

- 特徴量キャッシュの仕組み
  - 同一テーブル構造に対して特徴量再計算を省略可能とする設計

- モデル再学習用の教師データ構成
  - 入力（特徴量）＋正解ラベル（最適サンプル数）形式のログ保存



※ 実装段階では、上記仕様をもとにSQLビュー・Python側DataFrame構造として再整理を行う。  
　また、PostgreSQLバージョン差異や拡張統計の扱いについては、検証を通じて導入可否を判断する。



---


# 4.外部インターフェース（DB/API等）

本章では、本ツールが連携・依存する外部インターフェースについて整理する。  
主に PostgreSQL データベースとの接続仕様、および将来的に検討されているAPI連携の構想を示す。



### 1. データベースインターフェース（PostgreSQL）

#### 接続仕様

| 項目 | 内容 |
|------|------|
| 接続対象 | PostgreSQL 13 以上 |
| 接続方式 | `psycopg2` ライブラリによる直接接続（PostgreSQLとの親和性と安定性を重視） |
| 認証方式 | ユーザー名／パスワード（設定ファイルまたは環境変数） |
| 使用ポート | 5432（変更可能） |
| 接続要件 | `ANALYZE` 実行権限、該当スキーマへのSELECT権限、（必要に応じて）INSERT / UPDATE / DELETE 権限 |
| 対象外 | 外部テーブル（FDW）、INHERITSベースの継承テーブル |

#### 主なSQLインターフェース

| 機能 | 使用SQL・ビュー | 備考 |
|------|------------------|------|
| 統計情報取得 | `pg_stat_all_tables`, `pg_class`, `pg_stats`, `pg_attribute` 等 | クエリ対象テーブルに限定して取得 |
| 実行計画取得 | `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` | 学習フェーズのみ実行 |
| 統計情報更新 | `ANALYZE テーブル名` | 推定行数に応じて制御（全体 or 列単位） |
| テーブル情報取得 | `information_schema.tables`, `pg_namespace` 等 | 除外対象の判定に使用（スキーマ名・種別） |



### 2. モデル入出力インターフェース

| 項目 | 内容 |
|------|------|
| 保存形式 | Pickle または Joblib（scikit-learn 互換） |
| 保存タイミング | 学習フェーズ終了時にモデルファイルを保存 |
| 保存場所 | ローカルファイルシステム（初期）、将来的にS3等のクラウドストレージも視野 |
| 読み込み方式 | 適用フェーズ起動時に対象モデルファイルをロード |
| ファイル名構成 | `best_model.pkl`, `model_<timestamp>.pkl` など（切替管理を想定） |



### 3. 将来的なAPI／外部連携構想

#### API連携（想定）

| 機能 | 説明 |
|------|------|
| クエリ実行要求 | API経由でクエリを受け取り、サンプリング推定および `ANALYZE` を実行 |
| モデル可視化 | 学習済みモデルの特徴量重要度、構成などを返すAPI |
| 統計ログ出力 | 統計情報の履歴や推定値のログをJSONで返す |

#### Web UIとの接続想定

- フロントエンドはReactなどの軽量Webフレームワークを想定
- バックエンドはFlaskまたはFastAPI等で構成予定
- サンプル推定結果のグラフ表示、ログモニタリング画面などを構想



### 4. セキュリティ・権限に関する補足

- 接続ユーザーは、ANALYZEの実行権限を含む適切なDB権限を持つこと
- SQLインジェクション対策として、すべてのクエリにはパラメータバインドを使用
- ファイル保存パスは設定ファイルまたは環境変数から取得し、ハードコーディングは避ける
- 将来的にAPI連携を行う場合は、API認証・ロール制御・アクセス制限の導入が必須となる

---


# 5.AIによるサンプリング行数の推定ロジック

本章では、統計情報更新処理において、各テーブルに対して適切なサンプリング行数を推定するためのAIロジックの設計方針と実装概要を示す。

### 1. 目的

- `ANALYZE` 実行時における **過剰な全件スキャンの抑制** と、**統計精度の最適化** の両立を図る。
- テーブルごとに適切なサンプリング行数を推定し、処理時間と精度のバランスを最適化することを目的とする。



### 2. 推定手法

#### 基本手法

| 項目 | 内容 |
|------|------|
| モデル種別 | 回帰モデル（線形回帰、ランダムフォレスト、LightGBM 等を検証予定） |
| 入力（特徴量） | テーブル統計情報、構造情報、更新頻度、カラム統計など |
| 出力 | 推定されたサンプリング行数（整数値） |
| 実装ライブラリ | `scikit-learn`（初期段階）、将来的に `XGBoost`, `LightGBM` 等への切替も検討 |



### 3. 特徴量の例

以下の特徴量をベースとし、AIモデルに入力する：

- **テーブル全体統計**
  - `reltuples`（行数想定）
  - `relpages`（ブロック数）

- **更新・断片化**
  - `n_tup_upd`, `n_tup_ins`, `n_tup_del`, `n_dead_tup`

- **カラム統計**
  - `n_distinct`, `null_frac`, `correlation`（相関係数）

- **構造的特徴**
  - パーティション有無、インデックスの有無、カラム数



### 4. 推定値の制御と補正

- 最小・最大サンプリング行数にしきい値を設定し、過剰または極端な推定値を防止
- 以下のいずれかの条件に該当する場合は、既定値（default_statistics_target = 100 ※）にフォールバックする：
  - 特徴量取得に失敗した場合
  - モデルバージョンと特徴量スキーマが一致しない場合
  - 推定値が設定しきい値を大きく外れる場合

※ default_statistics_target = 100 の場合、内部的には最大で1カラムあたり約1万〜3万行程度がサンプリングされます（PostgreSQLの仕様に基づく）。


### 5. モデルの運用と更新

| 項目 | 内容 |
|------|------|
| 保存形式 | `joblib` または `pickle` |
| 保存単位 | モデルファイル（例：`best_model.pkl`）＋スキーマ情報（JSON形式） |
| 再学習 | 学習フェーズで定期的にログから再学習可能 |
| モデル切替 | タイムスタンプ or バージョン番号付きファイルで管理し、明示的な切替に対応 |



### 6. 備考

- 特徴量の設計とモデリングは拡張性を持たせ、将来的な精度改善やモデル種別の切替に柔軟に対応できる構造とする。
- 異常値やデータスパイクに対するロバスト性を確保するため、特徴量の正規化や外れ値補正のロジックも今後検討。


必要に応じて、CIパイプラインによるモデル精度検証や、モデル評価指標（RMSE、R² など）の記録も導入可能とする。


---

# 6.エラーハンドリング・ロギング

本章では、本ツールにおけるエラーハンドリングおよびロギングの方針について整理する。  
ツール全体の信頼性・保守性を高め、異常発生時の原因特定や再現性の確保を目的とする。



### 1. エラーハンドリング方針

| 種別 | 対応方針 | 備考 |
|------|----------|------|
| DB接続エラー | 即時ログ出力・リトライ後中断 | 接続タイムアウトや認証エラー等 |
| クエリ実行エラー | エラー内容を記録し対象をスキップ | SQL構文ミスや権限不足など |
| モデル読み込み失敗 | 既定値へのフォールバック | モデルファイル破損やパス不正など |
| 特徴量取得失敗 | 該当テーブルを除外・警告ログ | pg_stat等の情報取得不可時 |
| 推定値異常（極端値） | 最小／最大しきい値に強制補正 | 不正なサンプル数防止 |
| ファイルI/Oエラー | エラーログ記録・処理継続または中断 | JSON出力・モデル保存時など |
| 未知の例外 | トレース付きでログ記録後、中断 | 開発時のデバッグや障害調査に利用 |


### 2. ロギング設計

#### ログ出力の種類

| ログ種別 | 内容 | 出力例 |
|----------|------|--------|
| INFO | 通常処理の進行状況 | "Model loaded", "ANALYZE executed" |
| WARNING | 処理継続可能な軽微な異常 | "Missing statistics for table X" |
| ERROR | 処理の中断や影響のある異常 | "Failed to connect to DB", "Sampling estimation error" |
| DEBUG（任意） | 開発・検証用の詳細出力 | 特徴量の値、推定モデルの内部出力など |

#### ログ出力先

- コンソール（標準出力）
- ローカルファイル（初期は `logs/tool.log` 等）
- ローテーション設定（容量ベース、日次ベース）
- 将来的にクラウド連携（例：CloudWatch, Datadog 等）も視野

#### ログ出力形式

- JSON形式または整形済みテキストログ
- タイムスタンプ／ログレベル／処理対象／メッセージを含む形式  
  例：`[2025-06-24 10:00:00][INFO] Table=sales ANALYZE executed with 10000 rows`




### 3. 実装補足

- Pythonの`logging`モジュールを基盤とし、ログレベルや出力先は設定ファイルで制御可能
- クエリ単位でログをトレース可能なよう、クエリIDやテーブル名などを一貫して出力
- ログ設定はユニットテストやCI環境でも活用できるよう柔軟に構成する



### 4. 今後の拡張方針

- ログをJSON API経由で取得できるインターフェースの提供
- ログ解析・可視化のためのツール連携（Grafana, Kibana 等）
- エラーパターンに応じた通知機能（Slack連携、メール送信等）

---