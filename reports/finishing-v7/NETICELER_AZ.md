# V7: faydalı düzəlişlər və faktiki 5v5 nəticələri

148 tam nəzarətli yerli matç: 4 V6 uyğunluq yoxlaması, 40 ilkin seçim, 24 doğrulama, 80 əvvəl görünməmiş yekun oyun. Hər tərəf GK və dörd meydan oyunçusu ilə başlayır. Bütün əsas matçlarda hər iki tərəfin callback xətası və engine fallback sayı sıfırdır.

Əlavə 36 tamamlanmış ilkin pilot oyunu əsas nəticəyə qatılmayıb: oyun vaxtı olmayan payload üçün örtük yaddaşına qoruma əlavə edildi, sonra mənbə yenidən donduruldu. Əvvəlki kod və pilot logları arxivdə saxlanıb. Native fizika və taktika əmsalları bu düzəlişdə dəyişməyib.

## İlkin seçim

| Variant | Oyun | Q | H | M | Qollar | Qələbə |
|---|---:|---:|---:|---:|---:|---:|
| e_shot | 8 | 1 | 5 | 2 | 1:2 | 12.5% |
| e_cutback | 8 | 0 | 6 | 2 | 0:2 | 0% |
| e_off | 8 | 0 | 6 | 2 | 0:2 | 0% |
| e_balanced | 8 | 0 | 5 | 3 | 0:3 | 0% |
| e_cover | 8 | 0 | 5 | 3 | 0:3 | 0% |

## Ayrıca doğrulama

| Variant | Oyun | Q | H | M | Qollar | Qələbə |
|---|---:|---:|---:|---:|---:|---:|
| e_cutback | 8 | 2 | 2 | 4 | 2:5 | 25% |
| e_off | 8 | 2 | 2 | 4 | 2:5 | 25% |
| e_shot | 8 | 1 | 5 | 2 | 2:2 | 12.5% |

Seçilmiş yeni namizəd: **e_cutback**. Sıra əvvəlcədən qələbə → qol fərqi → vurulan qol → ad olaraq yazılıb. Son toxumlar 1401–1410-dur.

## Yekun nəticələr

| Variant / rəqib | Oyun | Q | H | M | Qollar | Qələbə |
|---|---:|---:|---:|---:|---:|---:|
| e_off / baseline | 20 | 1 | 17 | 2 | 2:3 | 5% |
| e_cutback / baseline | 20 | 1 | 17 | 2 | 2:3 | 5% |
| e_off / reference6 | 20 | 3 | 14 | 3 | 3:3 | 15% |
| e_cutback / reference6 | 20 | 3 | 14 | 3 | 3:3 | 15% |

Yeni variant qəbul şərtini keçmədi. V7-nin əsas profili V6 matç davranışını saxlayır; düzəlişlər ayrıca profillərdə işləyir.

Qələbə faizi fərqi 0 faiz bəndi; toxumları cüt saxlayan bootstrap 95% intervalı [0.0, 0.0]. Bu rəqəmlər canlı AWS turnirini qazanmaq ehtimalı deyil.

## Faktiki hücum göstəriciləri

| Variant | Zərbə | Pas | Geriyə pas | Son üçdəbirdə sahiblik tick |
|---|---:|---:|---:|---:|
| e_cutback | 146 | 1085 | 425 | 1898 |
| e_off | 146 | 1085 | 425 | 1898 |

## Şərh və istifadə

Yekun 40 cüt oyundan 40-də yeni və nəzarət variantının native hadisə faylı bayt-bayt eynidir. Bu, sınaq şəraitində davranış fərqinin nə qədər məhdud olduğunu göstərir. Bootstrap [0,0] çıxarsa belə, ümumi futbol təsirinin dəqiq sıfır olmasına sübut deyil.

Zərbə filtri bloklu zərbəni menyu və validatordan çıxarır; cutback prioriteti yalnız açıq, qapıya daha yaxın mərkəzi qəbul nöqtələrinə verilir; rəqib buraxılışından sonra örtük qısa görünən yaddaşla saxlanır. Bu texniki davranışların düzəlməsi avtomatik qələbə üstünlüyü demək deyil. `PATCHES_AZ.md` dəqiq hədləri və saxlanılan qoruyucuları izah edir.

Əsas yerli profil: `phase_tactics=attack`, `combination_tactics=give_go`, `finishing_tactics=off`. Pas ehtimalı modelinin `flow` sxeminə qoşulması texniki olaraq yoxlanıb, amma bütün bu matçlarda `use_pass_model=false` saxlanılıb. AUC qələbə ehtimalı deyil. Yeni model çəkiləri öyrədilməyib.

Müqayisə native baseline və dondurulmuş V6 agentimizlədir. AWS çempionlarına qarşı və canlı LLM ilə oyun yoxdur. Mühərrik, fizika, roster və atributlar dəyişdirilməyib. Mənbə əsas ilkin seçimdən son sınağa qədər dəyişdirilməyib. Əvvəlki versiyaların başqa toxumlarla ölçülmüş faizləri bu faizlərdən çıxılmamalıdır.
