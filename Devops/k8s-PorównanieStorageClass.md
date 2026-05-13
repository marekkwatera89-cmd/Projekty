# Benchmark Kubernetes Storage – NFS vs CephFS vs Ceph RBD pod PostgreSQL

## Wprowadzenie


Podczas projektowania platform Kubernetes dla aplikacji stanowych jednym z najważniejszych elementów architektury jest wybór odpowiedniego storage backendu.

Na pierwszy rzut oka większość systemów storage wygląda podobnie:
- udostępniają Persistent Volume,
- wspierają dynamic provisioning,
- mogą zostać podłączone do Podów.

W praktyce jednak zachowanie aplikacji — szczególnie baz danych takich jak PostgreSQL — bardzo mocno zależy od:
- opóźnień (latency),
- wydajności fsync,
- random I/O,
- synchronizacji metadanych,
- stabilności pracy pod obciążeniem.

W tym artykule porównuję trzy klasy storage używane w Kubernetes:

| Storage | Typ |
|---|---|
| NFS | współdzielony filesystem |
| CephFS | rozproszony filesystem |
| Ceph RBD | rozproszony block storage |

Celem benchmarku było określenie, który storage najlepiej nadaje się pod PostgreSQL działający w Kubernetes.

---

# Środowisko testowe

## Kubernetes

Środowisko testowe składało się z:
- klastra Kubernetes,
- CSI driverów,
- dynamic provisioning,
- Persistent Volume Claims 10Gi,
- benchmarków opartych o fio.

---

# Testowane klasy storage

## NFS

Klasyczny współdzielony filesystem.

### Zalety

- prostota,
- łatwość utrzymania,
- bardzo wysoki sequential throughput.

### Wady

- wysoka latency przy sync write,
- problemy z lockami,
- słabe zachowanie pod transactional workload.

---

## CephFS

Rozproszony POSIX-compatible filesystem.

### Zalety

- RWX,
- współdzielony storage,
- rozproszona architektura,
- dobra integracja z Kubernetes.

### Wady

- większy metadata overhead,
- niższy throughput niż block storage.

---

## Ceph RBD

Rozproszony block storage.

### Zalety

- bardzo dobre transactional IO,
- najlepszy kandydat pod bazy danych,
- wysoka stabilność pod obciążeniem.

### Wady

- ReadWriteOnce,
- bardziej zaawansowana architektura.

---

# Metodologia testów

Każdy backend storage otrzymał:
- osobny PVC 10Gi,
- dedykowanego benchmarkowego Poda,
- identyczne workloady fio.

Benchmark został zaprojektowany tak, aby symulować rzeczywiste zachowanie aplikacji.

---

# Kategorie testów

## 1. Sequential Write

Symuluje:
- backupy,
- upload dużych plików,
- media streaming,
- archiwizację.

### Konfiguracja fio

```bash
fio --name=seqwrite \
--directory=/data \
--rw=write \
--bs=1M \
--size=4G \
--numjobs=1 \
--iodepth=32 \
--direct=1
```

---

## 2. Sequential Read

Symuluje:
- streaming,
- backup restore,
- odczyt dużych plików,
- analitykę.

### Konfiguracja fio

```bash
fio --name=seqread \
--directory=/data \
--rw=read \
--bs=1M \
--size=4G \
--numjobs=1 \
--iodepth=32 \
--direct=1
```

---

## 3. Random Read 4k

Symuluje:
- index lookup,
- OLTP,
- cache miss,
- workload maszyn wirtualnych.

### Konfiguracja fio

```bash
fio --name=randread \
--directory=/data \
--rw=randread \
--bs=4k \
--size=2G \
--numjobs=4 \
--iodepth=32 \
--direct=1 \
--runtime=120 \
--time_based
```

---

## 4. Mixed Read/Write 70/30

Jeden z najważniejszych benchmarków.

Symuluje:
- bazy danych,
- workload Kubernetes,
- workload VM,
- aplikacje transactional.

### Konfiguracja fio

```bash
fio --name=randrw \
--directory=/data \
--rw=randrw \
--rwmixread=70 \
--bs=8k \
--size=2G \
--numjobs=4 \
--iodepth=32 \
--direct=1 \
--runtime=120 \
--time_based
```

---

## 5. PostgreSQL WAL / Sync Write Test

Najważniejszy benchmark całego porównania.

Test został zaprojektowany tak, aby możliwie wiernie symulować:
- PostgreSQL WAL,
- synchronous commit,
- fsync,
- transactional write.

### Konfiguracja fio

```bash
fio --name=pgkiller \
--directory=/data \
--rw=randwrite \
--bs=8k \
--size=512M \
--numjobs=16 \
--iodepth=1 \
--direct=1 \
--fsync=1 \
--runtime=300 \
--time_based \
--group_reporting
```

Ten benchmark bardzo dobrze symuluje rzeczywiste zachowanie PostgreSQL pod obciążeniem.

---

# Wyniki benchmarków

# Sequential Write

| Storage | Wynik |
|---|---|
| 🥇 Ceph RBD | ~270 MiB/s |
| 🥈 NFS | ~141 MiB/s |
| 🥉 CephFS | ~120 MiB/s |

## Interpretacja

Ceph RBD zdecydowanie wygrał test sequential write.

To naturalne zachowanie dla block storage:
- minimalny overhead,
- brak metadata coordination,
- bezpośredniejsza komunikacja z backend storage.

CephFS był najwolniejszy z powodu:
- POSIX semantics,
- metadata overhead,
- distributed filesystem coordination.

NFS osiągnął przyzwoity throughput, ale gorzej radził sobie pod sustained write pressure.

---

# Sequential Read

| Storage | Wynik |
|---|---|
| 🥇 NFS | ~810 MiB/s |
| 🥈 Ceph RBD | ~489 MiB/s |
| 🥉 CephFS | ~184 MiB/s |

## Interpretacja

NFS osiągnął bardzo wysoki sequential read throughput.

Ten workload bardzo korzysta z:
- cache,
- read-ahead,
- linear streaming.

Dlatego NFS świetnie sprawdza się jako:
- storage dla backupów,
- repozytorium multimediów,
- storage dużych plików.

Ceph RBD zachował bardzo dobrą wydajność przy jednoczesnym utrzymaniu distributed block storage semantics.

CephFS ponownie pokazał koszt dodatkowej warstwy filesystem abstraction.

---

# Random Read 4k

| Storage | Wynik |
|---|---|
| 🥇 NFS | ~20k IOPS |
| 🥈 Ceph RBD | ~16k IOPS |
| 🥉 CephFS | ~12k IOPS |

## Interpretacja

Benchmark symuluje:
- index lookup,
- OLTP,
- VM workload,
- cache miss.

NFS osiągnął bardzo dobre wyniki dla random read.

Należy jednak pamiętać, że random read:
- jest dużo łatwiejszy dla storage,
- nie wymaga fsync,
- nie powoduje transactional synchronization,
- mocno korzysta z cache.

Ceph RBD pokazał bardzo stabilne i przewidywalne zachowanie.

CephFS również osiągnął rozsądne wyniki mimo dodatkowej warstwy filesystem.

---

# Mixed Read/Write 70/30

| Storage | Read | Write |
|---|---|---|
| 🥇 Ceph RBD | ~56 MiB/s | ~24 MiB/s |
| 🥈 CephFS | ~45 MiB/s | ~19 MiB/s |
| 🥉 NFS | ~44 MiB/s | ~19 MiB/s |

## Interpretacja

To jeden z najbardziej realistycznych benchmarków.

Symuluje:
- bazy danych,
- StatefulSet,
- aplikacje transactional,
- workload VM.

I właśnie tutaj Ceph RBD wygrał bardzo wyraźnie.

To niezwykle ważna obserwacja.

Sequential benchmarki często bywają mylące.

Dopiero mixed workload pokazuje:
- real queue handling,
- synchronization overhead,
- metadata coordination,
- stabilność latency.

CephFS osiągnął zaskakująco dobre wyniki.

NFS stracił większość przewagi widocznej w sequential throughput.

---

# PostgreSQL WAL / Sync Write Test

## Najważniejszy benchmark

| Storage | Wynik |
|---|---|
| 🥇 CephFS | ~51 MiB/s |
| 🥈 Ceph RBD | ~47 MiB/s |
| 🔴 NFS | ~9 MiB/s |

---

# Dlaczego ten test jest najważniejszy?

Benchmark symuluje:
- PostgreSQL WAL,
- synchronous commit,
- fsync,
- transactional latency.

I właśnie tutaj wiele storage systemów zaczyna mieć problemy.

---

# Kluczowa obserwacja

NFS praktycznie się załamał.

Pomimo bardzo wysokiego sequential throughput wcześniejsze benchmarki pokazały, że przy transactional sync write NFS stał się niemal 5x wolniejszy.

Powodem są:
- synchronous ACK,
- metadata synchronization,
- network roundtrip,
- file locking,
- fsync overhead.

To właśnie dlatego PostgreSQL na NFS często cierpi na:
- wysoką commit latency,
- lock contention,
- checkpoint stalls,
- niestabilny TPS,
- latency spikes.

---

# CephFS – największe zaskoczenie benchmarku

CephFS osiągnął znacznie lepsze wyniki niż oczekiwałem.

Oznacza to:
- zdrową pracę MDS,
- stabilny cluster,
- dobrze działającą warstwę metadata.

CephFS okazał się bardzo mocnym kandydatem dla shared Kubernetes storage.

---

# Ceph RBD – najbardziej przewidywalny storage

Ceph RBD osiągnął bardzo stabilne wyniki we wszystkich benchmarkach.

To dokładnie dlatego distributed block storage jest standardem dla:
- PostgreSQL,
- MySQL,
- OpenStack,
- VMware,
- Kubernetes StatefulSet.

---

# Finalne porównanie

| Use Case | Najlepszy Storage |
|---|---|
| PostgreSQL | 🥇 Ceph RBD |
| Stateful Applications | 🥇 Ceph RBD |
| Virtual Machines | 🥇 Ceph RBD |
| Shared RWX Storage | 🥇 CephFS |
| Shared Application Data | 🥇 CephFS |
| Backupy | 🥇 NFS |
| Media Streaming | 🥇 NFS |
| Sequential Read | 🥇 NFS |

---

# Wnioski techniczne

## NFS

Świetny dla:
- backupów,
- mediów,
- dużych plików,
- prostego shared storage.

Słaby dla:
- transactional workload,
- baz danych,
- fsync-heavy applications.

---

## CephFS

Bardzo dobry kompromis pomiędzy:
- shared access,
- distributed storage,
- transactional behavior.

Bardzo dobry kandydat dla:
- RWX,
- shared Kubernetes storage,
- distributed applications.

---

## Ceph RBD

Najlepszy storage backend dla:
- PostgreSQL,
- baz danych,
- VM,
- Stateful workload.

Najbardziej stabilny i przewidywalny pod obciążeniem.

---

# Podsumowanie

Benchmark bardzo wyraźnie pokazał jedną ważną rzecz:

Wysoki throughput nie oznacza jeszcze, że storage nadaje się pod bazy danych.

Dla PostgreSQL najważniejsze są:
- latency stability,
- fsync behavior,
- transactional synchronization,
- random write handling.

Sequential benchmarki bardzo często premiują NFS.

Dopiero realistyczny transactional workload pokazuje prawdziwe zachowanie storage.

W tym scenariuszu Ceph RBD okazał się najbardziej stabilnym i najbardziej poprawnym architektonicznie rozwiązaniem pod PostgreSQL.

---

# Technologie wykorzystane w benchmarku

- Kubernetes
- Ceph
- CephFS
- Ceph RBD
- NFS
- CSI Drivers
- fio
- Persistent Volumes
- Stateful Workloads

---

# Autor

DevOps / Kubernetes / Storage Engineering

Specjalizacja:
- Kubernetes,
- storage architecture,
- observability,
- stateful workloads,
- high availability systems.

