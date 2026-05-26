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

Benchmark został zaprojektowany tak, aby możliwie realistycznie symulować zachowanie aplikacji działających w Kubernetes.

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
- intensywny random access workload.

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
- aplikacje transactional,
- StatefulSet workloads.

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

Ten benchmark bardzo dobrze odwzorowuje rzeczywiste zachowanie PostgreSQL pod obciążeniem.

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
- bardziej bezpośrednia komunikacja z backend storage.

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
- cache miss,
- intensywny random access workload.

NFS osiągnął bardzo dobre wyniki dla random read.

Należy jednak pamiętać, że random read:

- jest dużo łatwiejszy dla storage,
- nie wymaga fsync,
- nie powoduje transactional synchronization,
- bardzo mocno korzysta z cache.

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
- typowe workloady Kubernetes.

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
- Kubernetes StatefulSet,
- stateful workloads.

---

# Finalne porównanie

| Use Case | Najlepszy Storage |
|---|---|
| PostgreSQL | 🥇 Ceph RBD |
| Stateful Applications | 🥇 Ceph RBD |
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
- Stateful workload,
- aplikacji wymagających niskiej latency.

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
---
# Update 26.05.2026
---
# Dodanie nowego backendu storage

## Longhorn

Rozproszony Kubernetes-native block storage oparty o CSI.

### Zalety

- natywna integracja z Kubernetes,
- HA storage,
- snapshoty,
- replikacja danych,
- prosty deployment,
- łatwe recovery volume.

### Wady

- wyższe latency,
- duży overhead przy sync write,
- słabszy random I/O,
- wydajność zależna od sieci między node.

---

# Aktualizacja sekcji: Testowane klasy storage

| Storage | Typ |
|---|---|
| NFS | współdzielony filesystem |
| CephFS | rozproszony filesystem |
| Ceph RBD | rozproszony block storage |
| Longhorn | Kubernetes-native distributed block storage |

---

# Aktualizacja sekcji: Sequential Write

| Storage | Wynik |
|---|---|
| 🥇 Ceph RBD | ~270 MiB/s |
| 🥈 NFS | ~141 MiB/s |
| 🥉 CephFS | ~120 MiB/s |
| 4️⃣ Longhorn | ~48.3 MiB/s |

## Interpretacja

Longhorn osiągnął najniższy wynik w teście sequential write.

Powodem jest architektura distributed storage:

- synchronizacja replik,
- network replication,
- dodatkowa warstwa Longhorn engine,
- CSI overhead.

Każdy zapis:
1. trafia do Longhorn engine,
2. jest przesyłany przez sieć,
3. synchronizowany między replikami,
4. potwierdzany przez backend storage.

To powoduje wyraźnie wyższy koszt write workload niż w Ceph RBD.

Jednocześnie Longhorn zapewnia:
- HA,
- recovery,
- snapshoty,
- prosty deployment w Kubernetes.

---

# Aktualizacja sekcji: Sequential Read

| Storage | Wynik |
|---|---|
| 🥇 NFS | ~810 MiB/s |
| 🥈 Ceph RBD | ~489 MiB/s |
| 🥉 CephFS | ~184 MiB/s |
| 4️⃣ Longhorn | ~94.8 MiB/s |

## Interpretacja

Sequential read był wyraźnie szybszy niż sequential write, jednak Longhorn nadal osiągnął najniższy wynik spośród wszystkich backendów.

Mimo że read:
- nie wymaga synchronizacji write,
- korzysta z cache,
- jest mniej kosztowny niż transactional IO,

Longhorn nadal ponosi koszt:
- warstwy CSI,
- metadata handling,
- distributed block storage,
- sieciowej architektury storage.

Longhorn dużo lepiej radzi sobie z workload read-heavy niż write-heavy.

---

# Aktualizacja sekcji: Random Read 4k

| Storage | Wynik |
|---|---|
| 🥇 NFS | ~20k IOPS |
| 🥈 Ceph RBD | ~16k IOPS |
| 🥉 CephFS | ~12k IOPS |
| 4️⃣ Longhorn | ~3.4k IOPS |

## Interpretacja

Random Read 4k bardzo dobrze symuluje:
- PostgreSQL index lookup,
- OLTP,
- cache miss,
- małe operacje losowe.

To właśnie ten benchmark najlepiej pokazuje ograniczenia Longhorna.

Każda operacja:
- przechodzi przez Longhorn engine,
- korzysta z CSI,
- generuje dodatkowe latency,
- obciąża storage metadata.

Wysokie:
- queue depth,
- util,
- liczba operacji IO

pokazują pełne wysycenie backend storage.

Dla PostgreSQL oznacza to:
- wyższy query latency,
- wolniejsze indeksy,
- niższy throughput OLTP.

---

# Aktualizacja sekcji: Mixed Read/Write 70/30

| Storage | Read | Write |
|---|---|---|
| 🥇 Ceph RBD | ~56 MiB/s | ~24 MiB/s |
| 🥈 CephFS | ~45 MiB/s | ~19 MiB/s |
| 🥉 NFS | ~44 MiB/s | ~19 MiB/s |
| 4️⃣ Longhorn | ~15 MiB/s | ~6.5 MiB/s |

## Interpretacja

Mixed workload bardzo dobrze symuluje rzeczywiste zachowanie PostgreSQL.

To właśnie tutaj Longhorn pokazuje największy koszt architektury distributed replicated storage.

Każdy write:
- synchronizuje repliki,
- przechodzi przez sieć,
- wymaga acknowledgement,
- generuje dodatkowe latency.

W efekcie:
- write throughput był najniższy,
- queue depth bardzo wysoki,
- storage backend praktycznie stale wysycony.

Longhorn nadal zapewnia jednak:
- HA,
- persistence,
- recovery po awarii node,
- łatwe zarządzanie volume.

---

# Aktualizacja sekcji: PostgreSQL WAL / Sync Write Test

## Najważniejszy benchmark

| Storage | Wynik |
|---|---|
| 🥇 CephFS | ~51 MiB/s |
| 🥈 Ceph RBD | ~47 MiB/s |
| 🥉 Longhorn | ~11.3 MiB/s |
| 🔴 NFS | ~9 MiB/s |

## Interpretacja

To najważniejszy benchmark całego porównania.

Symuluje:
- PostgreSQL WAL,
- synchronous commit,
- fsync,
- transactional write.

Longhorn osiągnął wynik wyraźnie lepszy od NFS, jednak znacznie słabszy od CephFS oraz Ceph RBD.

Powodem jest:
- sync write replication,
- distributed acknowledgment,
- transactional latency,
- synchronizacja replik.

Każda operacja WAL:
1. musi zostać zapisana,
2. zsynchronizowana,
3. potwierdzona przez backend storage.

To powoduje ogromny wzrost:
- latency,
- queue depth,
- storage utilization.

Jednocześnie Longhorn nadal oferuje:
- HA,
- snapshoty,
- recovery,
- prostą integrację z Kubernetes.

---

# Aktualizacja sekcji: Finalne porównanie

| Use Case | Najlepszy Storage |
|---|---|
| PostgreSQL | 🥇 Ceph RBD |
| Stateful Applications | 🥇 Ceph RBD |
| Shared RWX Storage | 🥇 CephFS |
| Shared Application Data | 🥇 CephFS |
| Kubernetes-native HA Storage | 🥇 Longhorn |
| Homelab / Small Production | 🥇 Longhorn |
| Backupy | 🥇 NFS |
| Media Streaming | 🥇 NFS |
| Sequential Read | 🥇 NFS |

---

# Aktualizacja sekcji: Wnioski techniczne

## Longhorn

Bardzo dobry storage backend dla:

- Kubernetes-native environments,
- homelabów,
- małych i średnich środowisk,
- HA storage,
- prostego disaster recovery,
- StatefulSet workloads.

Słabszy dla:
- wysokiego IOPS,
- intensywnego OLTP,
- bardzo dużych baz PostgreSQL,
- workloadów fsync-heavy.

Największą zaletą Longhorna jest:
- prostota deploymentu,
- integracja z Kubernetes,
- łatwość recovery,
- distributed storage bez skomplikowanego Cepha.

Największym ograniczeniem pozostaje:
- write latency,
- random I/O,
- sync write overhead.

