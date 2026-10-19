# AEON — Архитектурный анализ, спецификация и рекомендации по развитию

> **Документ:** Архитектурный аудит и системная спецификация платформы AEON  
> **Версия:** 1.0.0  
> **Статус:** Анализ и рекомендации к проектированию  
> **Стек:** C# (.NET 9/10), SQL (PostgreSQL), Python (FastAPI), Vue 3 (TypeScript), Swift (iOS), Blockchain (EVM/BTC/Solana)

---

## Содержание

1. [Введение и общая оценка проекта](#1-введение-и-общая-оценка-проекта)
2. [Ключевые недочеты и неточности в исходной структуре](#2-ключевые-недочеты-и-неточности-в-исходной-структуре)
   - 2.1. Концептуальные пробелы: Custodial vs Non-Custodial и безопасность ключей
   - 2.2. Архитектура Backend (.NET) и отсутствие асинхронной обработки
   - 2.3. Дублирование и коллизии слоя базы данных
   - 2.4. Проблемы Blockchain Layer (RPC, реорганизации, UTXO vs Account)
   - 2.5. Сервис аналитики: протоколы взаимодействия и масштабируемость
   - 2.6. Web-клиент: смешение архитектурных подходов и отсутствие Web3-стека
   - 2.7. iOS-клиент: архитектура, безопасность и синхронизация контрактов
   - 2.8. Real-time коммуникации в P2P-сделках
   - 2.9. Организация тестирования и CI/CD
3. [Что необходимо добавить или переписать](#3-что-необходимо-добавить-или-переписать)
   - 3.1. Управление закрытыми ключами и транзакционная безопасность (KMS / MPC / Vault)
   - 3.2. Background Workers, Event-Driven архитектура и Message Broker
   - 3.3. Real-time движок (SignalR, WebSockets, Push Notifications)
   - 3.4. Машина состояний (State Machine) для P2P-платформы и эскроу
   - 3.5. Оптимизация структуры Web-клиента (Feature-Sliced Design / Clean Modular)
   - 3.6. Организация модулей тестирования (.NET, Web, iOS, Python)
4. [Оптимизированная эталонная структура репозитория](#4-оптимизированная-эталонная-структура-репозитория)
5. [Рекомендуемый технологический стек (по компонентам)](#5-рекомендуемый-технологический-стек-по-компонентам)
6. [План реализации и дорожная карта (Roadmap)](#6-план-реализации-и-дорожная-карта-roadmap)

---

## 1. Введение и общая оценка проекта

AEON задуман как многокомпонентный программный комплекс, объединяющий традиционный финтех (Web2), децентрализованные финансы (Web3) и анализ данных с оценкой рисков. 

**Сильные стороны исходной концепции:**
- Четкое разделение ответственности по языкам программирования и платформам (.NET для надежного ядра, Python для аналитики, Vue для веб, Swift для нативного мобильного опыта).
- Применение принципов Clean Architecture (API, Application, Domain, Infrastructure, Contracts) для серверной части.
- Выделение блокчейн-интеграций в отдельный слой абстракций.
- Вынос аналитического функционала в микросервис, предотвращающий загромождение ядра бэкенда тяжелыми Python-зависимостями.

Тем не менее, в представленной структуре и пояснительной записке содержится ряд существенных архитектурных «слепых зон», способных привести к критическим проблемам с безопасностью, производительностью и надежностью при реализации криптографических и P2P-операций.

---

## 2. Ключевые недочеты и неточности в исходной структуре

### 2.1. Концептуальные пробелы: Custodial vs Non-Custodial и безопасность ключей

**Недочет:**  
В описании декларируется работа с кошельками, транзакциями и блокчейн-сетями, но не определена **модель владения приватными ключами**:
1. **Custodial (кастодиальная модель):** Платформа владеет ключами пользователей.
   - *Проблема:* В структуре отсутствуют компоненты аппаратного или изолированного управления секретами (HSM, HashiCorp Vault, AWS KMS/GCP Cloud KMS, решения на базе Multi-Party Computation — MPC / Threshold Signatures). Хранить приватные ключи в реляционной SQL-базе (даже зашифрованными AES) категорически недопустимо в продакшене из-за рисков утечки, атак через SQL Injection и компрометации сервера приложений.
   - Отсутствует концепция Hot / Warm / Cold кошельков (для автоматических выплат, временного накопления и холодного хранения резервов).
2. **Non-Custodial (некастодиальная модель):** Пользователь единолично владеет seed-фразой / приватным ключом.
   - *Проблема:* В таком случае Backend **не имеет права** подписывать транзакции от имени пользователя. Блокчейн-сервис бэкенда должен выступать лишь индексатором (indexer), балансировщиком RPC-нод и валидатором входящих транзакций, а подпись должна выполняться строго на клиентах (iOS Secure Enclave / Keychain, Web Crypto API / Hardware Wallets).
3. **Smart Contract Wallets / Account Abstraction (ERC-4337):**
   - Если планируется современный Web3 UX (социальный вход, спонсирование газа, батчинг транзакций), требуются Bundler, Paymaster и EntryPoint контракты. В текущей структуре этого нет.

### 2.2. Архитектура Backend (.NET) и отсутствие асинхронной обработки

**Недочеты:**
1. **Отсутствие фоновых процессов (Background Workers / Outbox):**  
   Взаимодействие с блокчейном асинхронно по своей природе: отправка транзакции (broadcast), ожидание включения в блок (mempool), набор N подтверждений (confirmations), обработка возможных реорганизаций цепочки (chain reorgs). В структуре `src/backend/` есть только HTTP API (`AEON.Api`). Блокчейн-сканеры, слушатели событий смарт-контрактов и шедулеры не должны выполняться внутри процесса веб-сервера API. Необходим отдельный проект (или несколько) `AEON.Worker` / `AEON.BackgroundJobs`.
2. **Отсутствие шины сообщений / брокера очередей:**  
   Для надежной доставки событий (транзакция подтверждена, скоринг завершен, P2P ордер переведен в эскроу, отправлен пуш) необходим Message Broker (RabbitMQ, Apache Kafka, Redis Streams) и паттерн **Transactional Outbox**. Без этого при падении сервиса между записью в БД и вызовом внешнего API возникнет рассинхронизация данных.
3. **Отсутствие кэширования в памяти / распределенного кэша:**  
   В `AEON.Infrastructure` указан `Caching/`, но отсутствует конфигурация Redis / Dragonfly для распределенных блокировок (Distributed Locks для балансов и эскроу, предотвращение Double Spending на уровне API).

### 2.3. Дублирование и коллизии слоя базы данных

**Недочеты:**
- На уровне корня репозитория указана папка `database/` с `migrations/`, `views/`, `procedures/`, `scripts/`, а внутри `AEON.Infrastructure` одновременно указана `Persistence/Migrations/`.
- **Конфликт подходов:** Если используется Entity Framework Core (стандарт де-факто в .NET), миграции генерируются кодом C# в `AEON.Infrastructure`. Наличие дублирующей внешней папки `database/migrations/` порождает путаницу — какой инструмент является источником истины (EF Core Migrations, Flyway, DbUp или ручные SQL-скрипты)?
- **Хранимые процедуры (`procedures/`):** Использование хранимых процедур в современных архитектурах на Clean Architecture / DDD размывает бизнес-логику: часть правил окажется в процедурах SQL, а часть в `AEON.Domain` и `AEON.Application`. Это снижает тестируемость и усложняет аудит.

> Концептуальная и логическая модель данных платформы (57 сущностей, атрибуты, ключи, жизненные циклы, учёт средств) описана в [DATABASE.md](DATABASE.md).

### 2.4. Проблемы Blockchain Layer (RPC, реорганизации, UTXO vs Account)

**Недочеты:**
1. **RPC Resilience & Rate Limiting:**  
   Публичные и даже приватные RPC-ноды (Alchemy, QuickNode, Infura, Solana RPC) подвержены лимитам (Rate Limits), задержкам и сбоям. В блокчейн-модулях обязательно должны быть RPC Failover, Health Checks, Round-robin балансировка и Circuit Breaker.
2. **Различие моделей состояний (UTXO vs Account):**  
   - Bitcoin использует UTXO (Coin Selection, Change Outputs, управление непотраченными выходами, комиссии за байт/vB).
   - EVM использует Account-based модель (Nonces, EIP-1559 Base Fee + Priority Fee, смарт-контракты ERC-20/721).
   - Solana использует Account-based с Rent-exempt, Recent Blockhash и лимитом Compute Units.
   Унифицировать их через один интерфейс без глубокой специализации сложно. `AEON.Blockchain.Abstractions` должен проектироваться гибко, чтобы не навязывать Account-логику сети Bitcoin.
3. **Застрявшие транзакции (Stuck Transactions):**  
   Не предусмотрены механизмы ускорения транзакций: RBF (Replace-by-Fee) и CPFP (Child Pays for Parent) для Bitcoin, Speed-Up (повторная отправка с тем же nonce и увеличенным газом) для EVM.

### 2.5. Сервис аналитики: протоколы взаимодействия и масштабируемость

**Недочеты:**
1. **HTTP REST vs gRPC:**  
   Для межсервисного взаимодействия между .NET Backend и Python-сервисом аналитики REST/JSON является избыточно тяжелым и медленным форматом сериализации. Для синхронного скоринга транзакций в реальном времени рекомендуется **gRPC (Protocol Buffers)** с типизированными контрактами.
2. **Асинхронные тяжелые задачи:**  
   Анализ портфеля и рыночный прогноз — вычислительно емкие операции. При одновременном запросе 1000 пользователей синхронный HTTP приведет к Thread Starvation и таймаутам. Необходим асинхронный воркер задач (Celery / RQ / RabbitMQ consumer).
3. **Пакетный менеджер и пайплайн данных:**  
   В структуре Python указаны только общие папки. Отсутствуют спецификации зависимостей (`pyproject.toml` с `uv` или `poetry`), версии моделей, runtime-среда (ONNX Runtime / TensorRT для быстрого инференса без необходимости держать тяжелые фреймворки в памяти).

### 2.6. Web-клиент: смешение архитектурных подходов и отсутствие Web3-стека

**Недочеты:**
1. **Архитектурная каша в папке `src/`:**  
   Одновременно присутствуют: `components/`, `layouts/`, `pages/`, `views/`, `features/`.
   - `pages` и `views` — это синонимы в экосистеме Vue.
   - Совмещение классического слоя (`components`, `pages`) и фиче-ориентированного (`features`) приводит к тому, что разные разработчики складывают код в разные места.
   - **Решение:** Перейти на **Feature-Sliced Design (FSD)** или строгий **Modular/Domain Feature** подход (`features/<feature-name>/{components, api, stores, types}`).
2. **Полное отсутствие Web3-модулей:**  
   В структуре iOS есть `Core/Web3/`, а в веб-клиенте нет упоминания работы с провайдерами Web3 (EIP-6963, WalletConnect, Wagmi/Viem, Solana Wallet Adapter). Если планируется подключение MetaMask, Phantom, Rabby — в веб-клиенте должен быть модуль провайдеров кошельков.

### 2.7. iOS-клиент: архитектура, безопасность и синхронизация контрактов

**Недочеты:**
1. **Отсутствие шаблона архитектуры (UI/State):**  
   Для финтех/крипто-приложений со сложными переходами и строгими состояниями критически важно выбрать единый стандарт: The Composable Architecture (TCA) или Clean Swift / MVVM-C (Coordinator).
2. **Безопасность мобильного клиента:**  
   В папке `Security/` необходимо явно предусмотреть:
   - Jailbreak Detection (проверка взлома устройства);
   - SSL Pinning (защита от перехвата трафика MITM);
   - Secure Enclave и Biometric Authentication (Face ID / Touch ID) для авторизации операций и шифрования локального хранилища;
   - Защита скриншотов в фоне (Screen obfuscation при сворачивании).
3. **Ручное дублирование DTO/Contracts:**  
   Если в `AEON.Contracts` меняется контракт, в Swift и Vue его придется переписывать руками. Необходима генерация клиентов через OpenAPI / Swagger Codegen / Kiota.

### 2.8. Real-time коммуникации в P2P-сделках

**Недочет:**  
P2P-модуль включает в себя:
- Чат между покупателем и продавцом;
- Уведомления об изменении статуса сделки (депозит заморожен, оплата отправлена, средства освобождены, открыт диспут);
- Таймеры сделки (отсчет времени на оплату).
Использовать обычный REST polling здесь категорически нельзя (задержки, высокая нагрузка на сервер, риск пропустить истечение таймера). Необходим **SignalR Hub** в .NET и двустороннее WebSocket-соединение в веб и мобильном клиентах.

### 2.9. Организация тестирования и CI/CD

**Недочеты:**
- Корневая папка `tests/` с `unit/`, `integration/`, `e2e/`, `performance/` отделена от проектов. В экосистеме .NET тесты компилируются в отдельные сборки (`.csproj`), которые подключаются к решению (`.sln`).
- Тесты Python (`pytest`), тесты Vue (`Vitest`, `Playwright`) и тесты Swift (`XCTest`) имеют совершенно разный жизненный цикл и запуск. Складывать их в одну общую папку верхнего уровня нерационально.
- Отсутствуют каталоги CI/CD конфигураций (`.github/workflows/` или `.gitlab-ci.yml`).

---

## 3. Что необходимо добавить или переписать

### 3.1. Управление закрытыми ключами и транзакционная безопасность (KMS / MPC / Vault)

1. **Если система Custodial / Semi-Custodial:**
   - Вынести подписание транзакций в изолированный защищенный сервис **AEON.KeyManagement** (KMS / Vault).
   - Основной бэкенд формирует неподписанную транзакцию (Unsigned Transaction / Payload) и передает ее в Signer Service с проверкой лимитов, 2FA и политик безопасности (Policy Engine).
   - Ключи шифруются через Envelope Encryption (Master Key хранится в HSM/KMS).
2. **Если система Non-Custodial:**
   - Закрытые ключи никогда не покидают устройство пользователя.
   - Клиент запрашивает у бэкенда актуальный nonce/UTXO, комиссию газа, сериализованный payload.
   - Клиент подписывает транзакцию локально и передает подписанную транзакцию бэкенду для бродкаста в сеть (или бродкастит сам).

### 3.2. Background Workers, Event-Driven архитектура и Message Broker

Добавить в бэкенд:
- **`AEON.Workers`**:
  - `BlockchainScannerWorker`: отслеживает депозиты на адреса пользователей;
  - `TransactionConfirmationsWorker`: слушает блоки и дожидается необходимого количества подтверждений;
  - `P2POrderTimeoutWorker`: автоматически отменяет неоплаченные ордера по истечении времени;
  - `ExchangeRateSyncWorker`: обновляет курсы криптовалют и фиатных пар (CoinGecko, Binance, Chainlink).
- **Паттерн Transactional Outbox:** гарантирует, что событие публикуется в шину сообщений только при успешном коммите в SQL-базу.
- **Шина сообщений (RabbitMQ / MassTransit):** надежная передача событий между `AEON.Api`, `AEON.Workers` и внешними сервисами.

### 3.3. Real-time движок (SignalR, WebSockets, Push Notifications)

- Реализовать `AEON.Api/Hubs/`:
  - `P2PHub`: обмен сообщениями в сделке, мгновенная смена статусов, статус таймера;
  - `WalletHub`: мгновенное оповещение о поступлении депозита / изменении баланса;
  - `PriceFeedHub`: стриминг цен активов.
- Интеграция Firebase Cloud Messaging (FCM) и Apple Push Notification service (APNs) в `AEON.Infrastructure/Notifications/`.

### 3.4. Машина состояний (State Machine) для P2P-платформы и эскроу

Реализовать явный конечный автомат для P2P-сделок (например, на базе Stateless в .NET):
```
[Created] ──> [EscrowLocked] ──> [PaymentSent] ──> [Completed]
    │                │                 │
    ▼                ▼                 ▼
[Cancelled]      [Dispute]         [Dispute]
```
- **Арбитражная система (Admin/Dispute Resolution):** роли арбитров, загрузка доказательств (квитанции, скриншоты), принудительный возврат/выпуск средств из эскроу.

### 3.5. Оптимизация структуры Web-клиента (Feature-Sliced Design / Clean Modular)

Устранить дублирование `pages/views/features`. Рекомендуемая архитектура (Feature-Driven):
- `src/app/` — инициализация, провайдеры, роутер, глобальные стили;
- `src/features/` — вертикальные срезы бизнес-логики (`auth`, `wallet`, `p2p`, `trade`, `analytics`), внутри которых свои компоненты, сторы (Pinia), хуки и API;
- `src/shared/` — переиспользуемые UI-компоненты (дизайн-система), утилиты, Web3-коннекторы, HTTP-клиент.

### 3.6. Организация модулей тестирования (.NET, Web, iOS, Python)

Тесты должны быть колоцированы со своими технологическими стеками:
- .NET тесты внутри решения `.sln` в папке `tests/backend/` (`AEON.Domain.UnitTests`, `AEON.Application.IntegrationTests`, `AEON.Api.FunctionalTests`);
- Web-тесты внутри `src/web/aeon-web/tests/`;
- Тесты Python-сервиса внутри `src/analytics/AEON.Analytics/tests/`;
- iOS-тесты внутри `src/mobile/ios/AEONTests/` и `AEONUITests/`.
- В корневой папке `tests/` остаются только сквозные **E2E/System** и **Performance/Load** тесты (на базе k6, Playwright, Newman), тестирующие систему целиком в Docker-окружении.

---

## 4. Оптимизированная эталонная структура репозитория

```text
AEON/
│
├── .github/                              # CI/CD пайплайны и шаблоны
│   ├── workflows/
│   │   ├── backend-ci.yml
│   │   ├── analytics-ci.yml
│   │   ├── web-ci.yml
│   │   └── ios-ci.yml
│   └── pull_request_template.md
│
├── src/
│   │
│   ├── backend/                          # .NET 9/10 Clean Architecture Solution
│   │   ├── AEON.sln
│   │   │
│   │   ├── AEON.Api/                     # HTTP REST API & SignalR Hubs
│   │   │   ├── Controllers/
│   │   │   │   ├── v1/
│   │   │   ├── Hubs/                     # Real-time WebSocket Hubs (P2P, Wallets)
│   │   │   ├── Middleware/               # Auth, Exception handling, Rate limiting
│   │   │   ├── Filters/
│   │   │   ├── Extensions/
│   │   │   ├── Configuration/
│   │   │   ├── appsettings.json
│   │   │   └── Program.cs
│   │   │
│   │   ├── AEON.Workers/                 # Фоновые процессы и обработка очередей
│   │   │   ├── Blockchain/               # Сканнеры блоков и подтверждений
│   │   │   ├── P2P/                      # Тайм-ауты и эскроу-таймеры
│   │   │   ├── Consumers/                # MassTransit / RabbitMQ consumer'ы
│   │   │   └── Program.cs
│   │   │
│   │   ├── AEON.Application/             # Use Cases, CQRS (MediatR), Валидация
│   │   │   ├── Common/                   # Behaviors (Logging, Validation, Caching)
│   │   │   ├── Authentication/
│   │   │   ├── Users/
│   │   │   ├── Wallets/
│   │   │   ├── Assets/
│   │   │   ├── Transactions/
│   │   │   ├── P2P/                      # Логика ордеров, эскроу и диспутов
│   │   │   ├── Analytics/                # Интеграция аналитики и риск-скоринга
│   │   │   └── Notifications/
│   │   │
│   │   ├── AEON.Domain/                  # Чистая предметная область (No external deps)
│   │   │   ├── Common/                   # BaseEntity, AggregateRoot, ValueObject
│   │   │   ├── Entities/
│   │   │   ├── ValueObjects/             # CryptoAmount, Address, Currency
│   │   │   ├── Enums/
│   │   │   ├── Events/                   # Domain Events
│   │   │   ├── Exceptions/
│   │   │   └── StateMachines/            # Состояния P2P сделки и транзакций
│   │   │
│   │   ├── AEON.Infrastructure/          # Технические реализации интерфейсов
│   │   │   ├── Persistence/              # PostgreSQL + EF Core
│   │   │   │   ├── Context/
│   │   │   │   ├── Configurations/       # Fluent API конфигурации сущностей
│   │   │   │   ├── Repositories/
│   │   │   │   └── Migrations/
│   │   │   ├── KeyManagement/            # Интеграция с Vault / KMS (управление ключами)
│   │   │   ├── Messaging/                # Outbox, RabbitMQ, MassTransit
│   │   │   ├── Caching/                  # Redis, Distributed Locks
│   │   │   ├── ExternalServices/         # CoinGecko, Chainlink, KYC провайдеры
│   │   │   ├── Notifications/            # FCM, APNs, SMTP, Telegram Bot
│   │   │   └── Logging/                  # Serilog, OpenTelemetry
│   │   │
│   │   └── AEON.Contracts/               # Общие DTO и Protobuf контракты (API & gRPC)
│   │       ├── v1/
│   │       │   ├── Requests/
│   │       │   └── Responses/
│   │       └── Protos/                   # gRPC схемы для связи с сервисом аналитики и внешними модулями
│   │
│   ├── blockchain/                       # Независимый слой блокчейн-интеграций
│   │   ├── AEON.Blockchain.Abstractions/ # Унифицированные интерфейсы кошельков/RPC
│   │   │   ├── Interfaces/               # IRpcClient, IWalletService, ITransactionService
│   │   │   ├── Models/                   # BlockInfo, RawTransaction, GasEstimate
│   │   │   └── Exceptions/
│   │   │
│   │   ├── AEON.Blockchain.Bitcoin/      # Bitcoin Node RPC & UTXO Management
│   │   │   ├── Client/
│   │   │   ├── UtxoManager/              # Coin selection (Knapsack / Branch and Bound)
│   │   │   ├── Transactions/             # SegWit/Taproot builders, PSBT
│   │   │   └── Fees/                     # Mempool fee estimator
│   │   │
│   │   ├── AEON.Blockchain.EVM/          # Ethereum, Polygon, Arbitrum, BSC, etc.
│   │   │   ├── Client/                   # Nethereum / Custom RPC Failover Client
│   │   │   ├── Contracts/                # ERC-20, ERC-721, Escrow Smart Contracts
│   │   │   ├── Gas/                      # EIP-1559 Dynamic Fee Estimation
│   │   │   └── Transactions/             # Nonce management, Speed-up, Cancellation
│   │   │
│   │   └── AEON.Blockchain.Solana/       # Solana Web3 Client
│   │       ├── Client/                   # Solana RPC, WebSocket subscriber
│   │       ├── Instructions/             # SPL Token, System Program
│   │       └── Transactions/             # Compute Budget, Priority Fees, Blockhash
│   │
│   ├── analytics/                        # Python-сервис аналитики и скоринга
│   │   └── AEON.Analytics/
│   │       ├── app/
│   │       │   ├── core/                 # Конфигурация, безопасность, логи
│   │       │   ├── api/
│   │       │   │   ├── v1/               # FastAPI REST endpoints
│   │       │   │   └── grpc/             # Быстрый gRPC сервер для .NET бэкенда
│   │       │   ├── services/             # Бизнес-логика скоринга и прогнозирования
│   │       │   ├── engine/
│   │       │   │   ├── models/           # Экспортированные модели (ONNX, PyTorch)
│   │       │   │   ├── pipelines/        # Препроцессинг, Feature Engineering
│   │       │   │   └── training/         # Скрипты обучения и валидации
│   │       │   └── schemas/              # Pydantic схемы данных
│   │       ├── tests/
│   │       ├── pyproject.toml            # Poetry / uv спецификация пакетов
│   │       └── Dockerfile
│   │
│   ├── web/                              # Vue 3 Web Application (TypeScript)
│   │   └── aeon-web/
│   │       ├── src/
│   │       │   ├── app/                  # Инициализация приложения, провайдеры
│   │       │   ├── shared/               # Переиспользуемые компоненты, UI Kit, utils
│   │       │   │   ├── ui/               # Базовые UI-компоненты (Button, Modal, Input)
│   │       │   │   ├── api/              # HTTP / WebSocket клиент
│   │       │   │   ├── web3/             # WalletConnect, Wagmi/Viem, Solana Adapter
│   │       │   │   └── lib/              # Форматирование валют, дат, крипто-чисел
│   │       │   ├── features/             # Вертикальные модули бизнес-логики
│   │       │   │   ├── auth/             # Вход, 2FA, сессии
│   │       │   │   ├── wallet/           # Балансы, депозиты, выводы
│   │       │   │   ├── p2p/              # Список офферов, оформление сделки, чат
│   │       │   │   ├── analytics/        # Дашборд рисков, рекомендации
│   │       │   │   └── profile/          # KYC, безопасность, настройки
│   │       │   ├── pages/                # Роутинг и компоновка экранов
│   │       │   └── router/
│   │       ├── tests/
│   │       ├── package.json
│   │       ├── vite.config.ts
│   │       └── Dockerfile
│   │
│   └── mobile/                           # Нативные мобильные клиенты
│       └── ios/
│           └── AEON/
│               ├── App/                  # App Entry, Dependency Injection, Coordinators
│               ├── Core/
│               │   ├── Networking/       # REST, SignalR/WebSockets
│               │   ├── Security/         # Secure Enclave, Keychain, BioAuth, SSL Pinning
│               │   ├── Storage/          # SwiftData / GRDB, Encrypted Database
│               │   └── Web3/             # Нативные криптобиблиотеки, подпись (secp256k1, ed25519)
│               ├── Features/             # Модули (Auth, Wallet, P2P, Analytics, Profile)
│               ├── DesignSystem/         # Цвета, типографика, компоненты SwiftUI
│               ├── Resources/
│               └── Tests/                # XCTest, XCUITest
│
├── tests/                                # Сквозные и нагрузочные тесты всей платформы
│   ├── backend/                          # .NET Unit & Integration тесты решений
│   ├── e2e/                              # Playwright сквозные тесты Web + Backend
│   └── performance/                      # k6 сценарии нагрузочного тестирования
│
├── infrastructure/                       # DevOps и развертывание
│   ├── docker/
│   │   ├── docker-compose.yml            # Базовый стек для локальной разработки
│   │   ├── docker-compose.prod.yml       # Production конфигурация
│   │   └── env.example
│   ├── k8s/                              # Kubernetes манифесты (или Helm-чарты)
│   ├── nginx/
│   │   └── conf.d/                       # Reverse proxy, SSL, Rate limiting
│   ├── monitoring/
│   │   ├── prometheus/
│   │   ├── grafana/
│   │   └── loki/
│   └── vault/                            # Скрипты инициализации HashiCorp Vault
│
├── docs/                                 # Полная техническая документация
│   ├── architecture/                     # ADR (Architecture Decision Records)
│   ├── api/                              # OpenAPI/Swagger спецификации
│   ├── security/                         # Модели угроз, аудит смарт-контрактов
│   ├── blockchain/                       # Спецификации RPC и подтверждений
│   ├── database/                         # ER-диаграммы, схемы партиционирования
│   └── diagrams/
│       ├── c4/                           # C4 Model (Context, Containers, Components)
│       └── sequences/                    # Диаграммы P2P эскроу, транзакций
│
├── scripts/                              # Утилиты автоматизации и миграций
│   ├── setup-local-env.sh
│   ├── generate-contracts.sh             # Генерация TypeScript и Swift из DTO
│   └── backup-db.sh
│
├── .gitignore
├── README.md
└── LICENSE
```

---

## 5. Рекомендуемый технологический стек (по компонентам)

| Слой / Компонент | Рекомендуемые технологии | Обоснование |
|---|---|---|
| **Backend API** | .NET 9/10, ASP.NET Core Web API, SignalR | Высокая производительность, асинхронный I/O, строгая типизация, отличный DI |
| **CQRS & Логика** | MediatR, FluentValidation, Stateless | Чистая архитектура, легкое тестирование, надежный конечный автомат для P2P |
| **Фоновые задачи** | .NET BackgroundServices, MassTransit, Quartz.NET | Надежная обработка блокчейн-событий, retry-политики, Outbox |
| **База данных** | PostgreSQL 16+, EF Core 9, Dapper (для аналитики) | Надежность транзакций (ACID), поддержка JSONB для метаданных блокчейна, партиционирование |
| **Кэш и очереди** | Redis 7+ (StackExchange.Redis), RabbitMQ | Distributed locks для балансов, кэш котировок, надежный брокер сообщений |
| **Секреты и ключи** | HashiCorp Vault / AWS KMS | Изолированное хранение мастер-ключей и подписание транзакций без прямого доступа API |
| **Блокчейн EVM** | Nethereum, Web3.js / Viem | Проверенные временем клиенты для работы со смарт-контрактами и RPC |
| **Блокчейн BTC** | NBitcoin | Индустриальный стандарт .NET для работы с Bitcoin, SegWit, PSBT |
| **Блокчейн Solana**| Solnet / Custom RPC | Асинхронный клиент для взаимодействия с Solana |
| **Сервис аналитики** | Python 3.12, FastAPI, gRPC, ONNX Runtime, PyTorch | Скорость инференса, удобная интеграция с .NET через Protocol Buffers |
| **Web Frontend** | Vue 3, Vite, TypeScript, Pinia, Tailwind CSS, Viem | Быстрый бандлер, реактивность, строгие типы, современная Web3-интеграция |
| **iOS Mobile** | Swift 6, SwiftUI, Swift Concurrency (async/await), TCA | Современный декларативный UI, безопасность многопоточности, защита состояния |
| **Мониторинг** | OpenTelemetry, Prometheus, Grafana, Jaeger | Сквозная трассировка запросов через Web → API → Worker → Blockchain/Analytics |

---

## 6. План реализации и дорожная карта (Roadmap)

### Этап 1: Фундамент и Безопасность (Core Foundation)
1. Развертывание базовой инфраструктуры в Docker (PostgreSQL, Redis, RabbitMQ).
2. Настройка решения .NET (`AEON.sln`): Entity Framework Core, Fluent Migrations, базовые сущности (`User`, `Wallet`, `Asset`).
3. Определение модели ключей (Custodial + Vault vs Non-Custodial). Создание сервиса управления адресами.
4. Внедрение CI/CD для базовой проверки сборки и линтеров.

### Этап 2: Блокчейн-интеграции и Модуль кошельков (Blockchain Engine)
1. Реализация `AEON.Blockchain.Abstractions`.
2. Подключение EVM-сетей (Ethereum, Polygon, BSC): генерация депозитных адресов, сканирование блоков в `AEON.Workers`, подтверждение транзакций.
3. Подключение Bitcoin (UTXO-сканнер, SegWit) и Solana.
4. Разработка надежного механизма вывода средств (Withdrawal) с двухфакторным подтверждением и антифрод-проверками.

### Этап 3: P2P-платформа и Real-time взаимодействие (P2P Engine)
1. Разработка машины состояний для P2P-сделок (Stateless).
2. Смарт-контракт эскроу или внутренний балансовый Escrow-сервис с блокировкой активов.
3. Разработка SignalR Hub для мгновенного P2P-чата и обновления статусов в реальном времени.
4. Модуль разрешения споров (Dispute Management) для администраторов.

### Этап 4: Сервис аналитики и скоринга
1. Разработка микросервиса `AEON.Analytics` на Python с FastAPI + gRPC интерфейсом.
2. Подключение скоринга риска транзакций (проверка подозрительных адресов, AML, аномальные объемы).
3. Инструмент анализа криптопортфеля и формирования рекомендаций для пользователей.

### Этап 5: Клиентские приложения (Web & iOS)
1. Разработка дизайн-системы и интерфейса Web-клиента на Vue 3 (модули кошелька, P2P-биржи, панели аналитики).
2. Разработка нативного iOS-приложения на SwiftUI с интеграцией биометрии и Secure Enclave.
3. Автогенерация типизированных контрактов API для клиентов.

### Этап 6: Нагрузочное тестирование, аудит и запуск
1. Нагрузочное тестирование (k6) сценариев массовых депозитов, P2P-сделок и параллельных запросов.
2. Аудит безопасности: тестирование на проникновение (PenTest), аудит логики эскроу, проверка изоляции ключей.
3. Настройка мониторинга (Grafana, Alertmanager) и развертывание в производственной среде.

---

*Документ подготовлен для команды разработки AEON. Служит официальным архитектурным руководством.*
