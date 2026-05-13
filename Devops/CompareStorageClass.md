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

3. Sekwencyjny zapis
```
fio --name=seqwrite \
--directory=/data \
--rw=write \
--bs=1M \
--size=4G \
--numjobs=1 \
--iodepth=32 \
--direct=1
```
Wyniki:

```
CephFS:
Run status group 0 (all jobs):
  WRITE: bw=120MiB/s (126MB/s), 120MiB/s-120MiB/s (126MB/s-126MB/s), io=4096MiB (4295MB), run=34189-34189msec

CephRBD:

Run status group 0 (all jobs):
  WRITE: bw=270MiB/s (283MB/s), 270MiB/s-270MiB/s (283MB/s-283MB/s), io=4096MiB (4295MB), run=15156-15156msec

Disk stats (read/write):
  rbd1: ios=0/4101, sectors=0/8370864, merge=0/72, ticks=0/14831, in_queue=14831, util=97.29%

NFS:
Run status group 0 (all jobs):
  WRITE: bw=141MiB/s (148MB/s), 141MiB/s-141MiB/s (148MB/s-148MB/s), io=4096MiB (4295MB), run=29030-29030msec
```

CephRBD zwycięzca. 270 MiB wynik sekwencyjnego zapisu. W Porównnaiu do NFS 141 oraz CephFS 120MB.


4. Sekwencyjny odczyt
```
fio --name=seqread \
--directory=/data \
--rw=read \
--bs=1M \
--size=4G \
--numjobs=1 \
--iodepth=32 \
--direct=1
```

Wyniki:
nfs:

Run status group 0 (all jobs):
   READ: bw=810MiB/s (850MB/s), 810MiB/s-810MiB/s (850MB/s-850MB/s), io=4096MiB (4295MB), run=5055-5055msec

cephrbd:
Run status group 0 (all jobs):
   READ: bw=489MiB/s (512MB/s), 489MiB/s-489MiB/s (512MB/s-512MB/s), io=4096MiB (4295MB), run=8384-8384msec

Disk stats (read/write):
  rbd1: ios=4078/2, sectors=8351744/24, merge=0/1, ticks=8216/8, in_queue=8223, util=97.04%

cephfs:
Run status group 0 (all jobs):
   READ: bw=184MiB/s (193MB/s), 184MiB/s-184MiB/s (193MB/s-193MB/s), io=4096MiB (4295MB), run=22240-22240msec

Zwycięzca NFS - mocny dla dużych plików, backupów, archiwów. Ceph RBD - najbardziej uniwesralny VM, DB. CephFS - rwx, wiele klientów, 

5. Random Read 4k
```
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
Wyniki:
```
RBD:

Run status group 0 (all jobs):
   READ: bw=63.6MiB/s (66.7MB/s), 15.8MiB/s-16.0MiB/s (16.6MB/s-16.7MB/s), io=7637MiB (8008MB), run=120001-120001msec

Disk stats (read/write):
  rbd1: ios=1952793/10, sectors=15622352/208, merge=0/16, ticks=449358/13, in_queue=449371, util=100.00%

NFS:
Run status group 0 (all jobs):
   READ: bw=80.3MiB/s (84.2MB/s), 13.3MiB/s-22.3MiB/s (14.0MB/s-23.4MB/s), io=9639MiB (10.1GB), run=120001-120001msec

CephFS:

Run status group 0 (all jobs):
   READ: bw=47.9MiB/s (50.2MB/s), 11.9MiB/s-12.0MiB/s (12.5MB/s-12.6MB/s), io=5742MiB (6021MB), run=120001-120002msec

Wynik:
NFS: 80 Mib = ≈ 20 000 IOPS
RBD: 63 Mib = ≈ 16 000 IOPS
CephFS: 48 Mib = ≈ 12 000 IOPS

IOPS = MB/s * 1024 / 4



```

6. Mixed Random 70/30
```
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

Wyniki:
```
nFS:
Run status group 0 (all jobs):
   READ: bw=44.6MiB/s (46.7MB/s), 9659KiB/s-11.7MiB/s (9891kB/s-12.3MB/s), io=5347MiB (5607MB), run=120001-120001msec
  WRITE: bw=19.2MiB/s (20.1MB/s), 4132KiB/s-5172KiB/s (4231kB/s-5296kB/s), io=2298MiB (2410MB), run=120001-120001msec

RBD:
Run status group 0 (all jobs):
   READ: bw=56.6MiB/s (59.3MB/s), 14.1MiB/s-14.2MiB/s (14.8MB/s-14.9MB/s), io=6790MiB (7120MB), run=120001-120001msec
  WRITE: bw=24.3MiB/s (25.5MB/s), 6197KiB/s-6271KiB/s (6345kB/s-6422kB/s), io=2921MiB (3063MB), run=120001-120001msec

Disk stats (read/write):
  rbd1: ios=868973/373902, sectors=13903568/5982304, merge=0/38, ticks=220914/238452, in_queue=459366, util=99.97%


CEPHFS:
Run status group 0 (all jobs):
   READ: bw=45.6MiB/s (47.8MB/s), 11.4MiB/s-11.4MiB/s (11.9MB/s-12.0MB/s), io=5468MiB (5734MB), run=120001-120001msec
  WRITE: bw=19.6MiB/s (20.5MB/s), 5002KiB/s-5030KiB/s (5122kB/s-5151kB/s), io=2351MiB (2465MB), run=120001-120001msec

```

Wyniki
Storage	Read	Write
NFS	~44.6 MiB/s	~19.2 MiB/s
RBD	~56.6 MiB/s	~24.3 MiB/s
CephFS	~45.6 MiB/s	~19.6 MiB/s


7. Wall / PostgreSQL killer test
```
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

Wyniki:
```
cephfs
Run status group 0 (all jobs):
  WRITE: bw=51.1MiB/s (53.6MB/s), 51.1MiB/s-51.1MiB/s (53.6MB/s-53.6MB/s), io=15.0GiB (16.1GB), run=300003-300003msec

cephrbd:
Run status group 0 (all jobs):
  WRITE: bw=47.0MiB/s (49.3MB/s), 47.0MiB/s-47.0MiB/s (49.3MB/s-49.3MB/s), io=13.8GiB (14.8GB), run=300002-300002msec

Disk stats (read/write):
  rbd1: ios=0/2320901, sectors=0/48537720, merge=0/1941780, ticks=0/1639653, in_queue=1639653, util=96.84%

nfs:
Run status group 0 (all jobs):
WRITE: bw=9331KiB/s (9555kB/s), 9331KiB/s-9331KiB/s (9555kB/s-9555kB/s), io=2734MiB (2866MB), run=300009-300009msec
```

CephFS: 51 mib/s, RBD: 47 Mib,s NFS: 9 mib (najslabiej, nfs sie zalamal)

Porównanie
Storage	Relative performance
CephFS	~5.5x szybszy
RBD	~5x szybszy
NFS	dramatyczny spadek
I TO jest właśnie problem PostgreSQL na NFS

Nie throughput sequential.

Tylko:

sync random write latency
