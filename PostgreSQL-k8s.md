# PostgreSQL Storage Benchmark – NFS vs CephFS vs Ceph RBD vs VM

## Wprowadzenie

Podczas projektowania platform Kubernetes dla aplikacji stanowych kluczowym elementem jest odpowiedni dobór storage backendu. Jeden z moich klientów po uruchomieniu PostgreSQL na Kubernetes zaczął zgłaszać problemy z wydajnością, głównie związane z wysoką latency i spowolnieniem transakcji. Na etapie projektowania środowiska przewidziano wyłącznie storage oparty o NFS StorageClass, który początkowo wydawał się wystarczający. PostgreSQL jest jednak bardzo wymagającym workloadem, dla którego dużo ważniejsze od samego throughput są fsync, random write oraz transactional latency. W związku z tym przygotowałem benchmark porównujący NFS, CephFS, Ceph RBD oraz klasyczną maszynę wirtualną, aby sprawdzić, które rozwiązanie najlepiej nadaje się pod PostgreSQL.

| Storage | Typ |
|---|---|
| NFS | Shared filesystem |
| CephFS | Distributed filesystem |
| Ceph RBD | Distributed block storage |
| VM | Klasyczna maszyna wirtualna |

Celem było sprawdzenie:
- który storage najlepiej nadaje się pod PostgreSQL,
- jak zachowuje się Kubernetes względem klasycznej VM,
- jak wygląda transactional workload.

---

# Środowisko testowe

- Kubernetes + CSI
- CephFS
- Ceph RBD
- NFS
- PVC 10Gi
- fio benchmark
- Klasyczna VM 

---

# Testy

## Sequential Write

### Polecenie

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

### Wyniki

| Storage | Wynik |
|---|---|
| 🥇 Ceph RBD | ~270 MiB/s |
| 🥈 VM | ~222 MiB/s |
| 🥉 NFS | ~141 MiB/s |
| CephFS | ~120 MiB/s |

### Wniosek

Ceph RBD najlepiej radził sobie z dużym liniowym zapisem.

---

# Sequential Read

### Polecenie

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

### Wyniki

| Storage | Wynik |
|---|---|
| 🥇 NFS | ~810 MiB/s |
| 🥈 Ceph RBD | ~489 MiB/s |
| 🥉 VM | ~213 MiB/s |
| CephFS | ~184 MiB/s |

### Wniosek

NFS świetnie sprawdza się przy:
- backupach,
- mediach,
- dużych plikach.

---

# Random Read 4k

### Polecenie

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

### Wyniki

| Storage | Wynik |
|---|---|
| 🥇 NFS | ~20k IOPS |
| 🥈 Ceph RBD | ~16k IOPS |
| 🥉 CephFS | ~12k IOPS |
| VM | ~8k IOPS |

### Wniosek

Ceph RBD zachowywał najbardziej stabilne wyniki pod random workload.

---

# Mixed Read/Write 70/30

### Polecenie

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

### Wyniki

| Storage | Read / Write |
|---|---|
| 🥇 Ceph RBD | ~56 / 24 MiB/s |
| 🥈 CephFS | ~45 / 19 MiB/s |
| 🥉 NFS | ~44 / 19 MiB/s |
| VM | ~39 / 16 MiB/s |

### Wniosek

To najbardziej realistyczny benchmark.

Tutaj Ceph RBD wyraźnie wygrał.

---

# PostgreSQL WAL / Sync Write Test

Najważniejszy benchmark całego porównania.

Symuluje:
- WAL,
- fsync,
- transactional write,
- synchronous commit.

### Polecenie

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

### Wyniki

| Storage | Wynik |
|---|---|
| 🥇 CephFS | ~51 MiB/s |
| 🥈 Ceph RBD | ~47 MiB/s |
| 🔴 NFS | ~9 MiB/s |
| 🔴 VM | ~9 MiB/s |

---

# Najważniejsze wnioski

## Ceph RBD

Najbardziej stabilny i przewidywalny storage.

Najlepszy wybór dla:
- PostgreSQL,
- StatefulSet,
- transactional applications.

---

## CephFS

Największe zaskoczenie benchmarku.

Bardzo dobre transactional wyniki jak na distributed filesystem.

Dobry wybór dla:
- RWX,
- shared Kubernetes storage.

---

## NFS

Świetny dla:
- backupów,
- mediów,
- dużych plików.

Słaby dla:
- PostgreSQL,
- sync write,
- transactional workload.

---

## VM vs Kubernetes

Kubernetes + Ceph RBD osiągał wyniki lepsze niż klasyczna VM.

Nowoczesny Kubernetes + CSI block storage:
- ma niski overhead,
- bardzo dobrze radzi sobie z transactional workload,
- nadaje się pod production PostgreSQL.

---

# Finalna rekomendacja

| Use Case | Najlepszy Storage |
|---|---|
| PostgreSQL | 🥇 Ceph RBD |
| Stateful Applications | 🥇 Ceph RBD |
| Shared RWX Storage | 🥇 CephFS |
| Backup / Media | 🥇 NFS |

---

# Podsumowanie

Najważniejszy wniosek:

Wysoki throughput nie oznacza jeszcze dobrego storage dla PostgreSQL.

Dla baz danych najważniejsze są:
- latency,
- fsync,
- transactional consistency,
- random write handling.

W tym benchmarku najlepszym rozwiązaniem pod PostgreSQL okazał się:

## 🥇 Kubernetes + Ceph RBD

