# K8S czy tylko dynamiczne Pody ? 

## Weryfikacja wydajności pod kątem Storage Class. Założenia
- Testujemy: CephFS, CephRBD, NFS

### Testy

1. Przetestowanie wydajności zapisu dysku (utworzenie pliku - o rozmiarze 4 GB wypełnionego zerami)

```
dd if=/dev/zero of=/data/test.img bs=1M count=4096 oflag=direct
```
NFS - 4294967296 bytes (4.3 GB, 4.0 GiB) copied, 8.85752 s, 485 MB/s
CEPHRBD - 4294967296 bytes (4.3 GB, 4.0 GiB) copied, 15.1631 s, 283 MB/s
CEPHFS - 4294967296 bytes (4.3 GB, 4.0 GiB) copied, 33.8757 s, 127 MB/s

Wnioski - NFS dobrze sobie radzi z dużym squenital write. 
CephRBD - OK wynik dla distributed replicated storage,
CEPHFS - słabiej ale RWX kosztuje performance.


2. fio (Flexible I/O Tester)  narzędzie do precyzyjnego badania wydajności dysku.
To konkretne polecenie symuluje losowy zapis małych porcji danych, co jest najbardziej wymagającym zadaniem dla każdego dysku (tak działają bazy danych czy systemy operacyjne).
```
fio --name=randwrite \
--directory=/data \
--rw=randwrite \
--bs=8k \
--size=512M \
--numjobs=1 \
--iodepth=16 \
--direct=1 \
--runtime=120 \
--time_based \
--fsync=1
```

NFS

<img width="1022" height="539" alt="obraz" src="https://github.com/user-attachments/assets/4ea370ff-e4d2-444b-a936-837dfadd2371" />

RBD

<img width="1039" height="595" alt="obraz" src="https://github.com/user-attachments/assets/965d9f07-a977-4e5d-b8c7-69d29acf1395" />

CEPHFS

<img width="1061" height="573" alt="obraz" src="https://github.com/user-attachments/assets/396b39b5-55b8-4eea-a532-4767385356e2" />

Wnioski

<img width="676" height="634" alt="obraz" src="https://github.com/user-attachments/assets/174e9fa6-1e22-42f0-9255-797d9d06e690" />


Ceph RBD - najlepszy dla PostgreSQL, MySQL, Mongi, VMdisk, StatefullSet bo:
block storage, przewidwywalne latency, dobre fsync, lepszy transation IO

Ceph FS - najlepsze dla współdzielonych danych, Worpress upload, logów, aplikacji wymagających RWX bo:
natywne RWX, HA, distrubuted filesystem

NFS - najlepszy do dużych transferów i backupów. Ndajelpiej do backupów, dumpów, Bo:
niski overhead, prostota, 
