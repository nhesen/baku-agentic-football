# İngilis məşqçi mənbələri əsasında V6 sınağı

15 məqalə/məşq/tədqiqat mənbəsinin qeydləri `RESEARCH_AZ.md` faylındadır. Üç yeni fikir ayrıca və birlikdə yoxlanıldı: ayrı ötürmə bucaqları, pasdan sonra qaçış, gecikdirmə və örtük müdafiəsi. Hər tərəf bir qapıçı və dörd meydan oyunçusu ilə başlayır.

180 tam yerli matç: 4 V5 uyğunluq yoxlaması, 60 ilkin seçim, 36 doğrulama, 80 əvvəl görünməmiş yekun matç. Bütün matçlarda hər iki tərəfin callback xətası və engine fallback sayı sıfırdır.

## İlkin seçim

| Variant | Oyun | Q | H | M | Qollar | Qələbə |
|---|---:|---:|---:|---:|---:|---:|
| c_give_go | 12 | 2 | 8 | 2 | 2:2 | 16.67% |
| c_off | 12 | 1 | 11 | 0 | 1:0 | 8.33% |
| c_screen | 12 | 1 | 10 | 1 | 1:1 | 8.33% |
| c_combined | 12 | 1 | 8 | 3 | 1:4 | 8.33% |
| c_triangles | 12 | 0 | 11 | 1 | 0:1 | 0% |

## Ayrıca doğrulama

| Variant | Oyun | Q | H | M | Qollar | Qələbə |
|---|---:|---:|---:|---:|---:|---:|
| c_off | 12 | 3 | 8 | 1 | 3:1 | 25% |
| c_give_go | 12 | 1 | 10 | 1 | 2:2 | 8.33% |
| c_screen | 12 | 0 | 11 | 1 | 0:1 | 0% |

Doğrulamada seçilən yeni variant: **c_give_go**. Seçmə qaydası əvvəlcədən dondurulub: qələbə, qol fərqi, vurulan qol, ad. Yekun toxumlar 1201–1210; hər variant/rəqib üçün hər iki tərəf yoxlanıb.

## Yekun nəticə

| Variant / rəqib | Oyun | Q | H | M | Qollar | Qələbə |
|---|---:|---:|---:|---:|---:|---:|
| c_off / baseline | 20 | 2 | 13 | 5 | 2:5 | 10% |
| c_give_go / baseline | 20 | 3 | 14 | 3 | 4:4 | 15% |
| c_off / reference5 | 20 | 4 | 12 | 4 | 4:4 | 20% |
| c_give_go / reference5 | 20 | 4 | 13 | 3 | 4:3 | 20% |

Yeni variant qəbul şərtini keçdi və əsas profilə seçildi.

Ümumi qələbə fərqi 2.5 faiz bəndi; cüt toxumlarla bootstrap 95% intervalı [-10.0, 15.0]. AWS turnirini qazanmaq ehtimalı kimi şərh edilə bilməz.

## Faktiki hücum göstəriciləri

| Variant | Zərbə | Pas | Geriyə pas | Son üçdəbirdə sahiblik tick |
|---|---:|---:|---:|---:|
| c_give_go | 129 | 1038 | 403 | 1680 |
| c_off | 138 | 1040 | 384 | 1901 |

## Dərs və sərhədlər

İnsan futbolundakı əsaslı prinsip simulyatorda avtomatik üstünlük yaratmır. Mövqe dəyişməsi təhlükəsiz pası, zərbə vaxtını və ötürmənin qəbulunu da dəyişə bilər. İlkin dəstdə bucaqlı dəstək 50 zərbə yaradıb, amma qol vurmayıb; birləşdirilmiş paket üç dəfə məğlub olub. Pasdan sonra qaçışın iki ilkin qələbəsi onun sabit üstünlüyünə sübut deyil. Bu müqayisə ayrıca müdaxilə səbəbinə tam sübut deyil; yeni paketlər sığorta rolunun aktiv oyunçuya keçirilməsi düzəlişini də paylaşır.

`PASS_OBSERVATIONS.jsonl` qəbul olunmuş native pasların müşahidələrini saxlayır; `PASS_SUMMARY.json` növbəti 60 tick-də topun bizə qayıtmasını sayır. Hadisə jurnalı dəqiq qəbul edənin kimliyini hər zaman vermir. Bu göstərici tam pas dəqiqliyi və ya yaradılmış sintetik məlumat deyil. Yeni ML çəkiləri bu mərhələdə öyrədilməyib.

Rəqiblər açıq native baseline və dondurulmuş öz V5 agentimizdir. Köhnə AWS çempionlarının kodu, canlı portal və LLM matçları bu sınağa daxil deyil. Fizika, atributlar və əmrlər dəyişdirilməyib; yalnız görünən müşahidələrdən qərar verilir. Yeni kod ilk seçimdən yekun sınağa qədər dəyişdirilməyib.

Əsas tövsiyə: `phase_tactics=attack`, `combination_tactics=give_go`. Hücum genişliyi və dərinliyi artıq V5-dən gəlir; sınaqdan keçməyən bütün xüsusiyyətlər əsas profilə birləşdirilmir.
