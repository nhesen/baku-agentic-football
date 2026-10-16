# V5: fazaya görə dəyişən 5v5 futbol

Komandada bir qapıçı və dörd meydan oyunçusu var. Düzülüş adındakı rəqəmlər yalnız dörd meydan oyunçusunu sayır. Bu sistem futbol prinsiplərindən qurulmuş qaydalardır; yeni PPO/IMPALA neyron şəbəkəsinin təlimi deyil. Müəllim nümunələri kodun yoxlanılan qərar qaydalarına çevrilib, onların faydası ayrıca native matçlarda ölçülür.

## Hücum və müdafiə eyni sxem deyil

| Vəziyyət | Kodun verdiyi cavab |
|---|---|
| Top bizdə, öz üçdəbirimizdəyik | 1–2–1: iki diaqonal çıxış və irəlidə pivot; məcburi ötürmə sayı yoxdur. |
| Top orta və irəli zonadadır | 1–1–2: topa yaxın birləşdirici, ayrı kanallarda fərqli dərinlikli qaçışlar. |
| Hücumun son zonası | Uzaq cinah oyunçusu daha mərkəzi zərbə/geriyə ötürmə zonasına yaxınlaşır. Bu, hazır kombinasiya və ya məcburi cutback əmri deyil. |
| Arxa oyunçu top aparır | Başqa oyunçu topun arxasını sığortalayır. Qapıçı hücumçuya çevrilmir. |
| Topu yeni qazandıq | Dörd saniyəlik müşahidə pəncərəsində irəli qaçışlar və qısa birləşdirici. Bu rəqəm sınaq parametridir, FIFA-nın universal qaydası deyil. |
| Rəqibdə top var | Yığcam iki müdafiə xətti, top tərəfinə sürüşmə, təhlükəli mərkəzi rəqiblərin qapı tərəfdən tutulması. |
| Rəqib öz qapımıza yaxınlaşır | Daha alçaq və dar blok. Hər oyunçunun rəqibin arxasınca uzaq cinaha getməsinə yol verilmir. |
| Yerli əks-press mümkündür | Top itkisindən sonrakı üç saniyədə ən az iki yaxın tərəfdaş, arxada sığorta və kifayət qədər enerji tələb edilir. Yalnız bir oyunçu birbaşa topa gedir. |
| Əks-press alınmır | Pəncərə bitəndə blok bərpa edilir. Hamının eyni anda topu təqib etməsi əmr edilmir. |
| Top cinaha çıxır | Yaxın presser, arxada örtük və məsafə şərti varsa təzyiq artırılır. |
| Komanda yorulub | Yüksək press dayandırılır; fərdi sprintin mövcud stamina qoruyucusu saxlanır. |
| Son hissədə irəlidəyik / geridəyik | Yalnız payload-da qalan vaxt məlumdursa daha qoruyucu / riskli yerləşmə; oyunun müddəti təxmin edilmir. |
| Top sahibi bilinmir / restart | Təhlükəsiz yerləşmə və əvvəlki restart qaydaları; uydurma sahiblik və açıq oyuna aid press tətbiq edilmir. |

Mövqelər xəritəyə çəkilmiş sabit şəkil deyil: görünən vəziyyətə görə hesablanan hərəkət hədəfləridir. Rəqibin mövqeyi, topun zonası, ötürmə xəttinin açıqlığı, topdan məsafə, istiqamət, ofsayd həddi, sahiblik keçidi, arxada örtük, aktiv oyunçu sayı, stamina, hesab və vaxt nəzərə alınır. `opponents_pressing_ball` ayrıca diaqnostikadır; hazırkı versiyada bütün müşahidə göstəriciləri ayrıca qərar şərti kimi istifadə edilmir.

Dörd oyunçunun tapşırığı görünən eyni snapshot əsasında deterministik hesablanır. Birbaşa rəqiblə təmasda köhnə `PRESS_BALL` əmri işləyir; uzaqdan yaxınlaşma üçün əvvəl yeni istiqamətləndirilmiş `MOVE_TO` işləyir. Agentlərin öz aralarında şəbəkə əlaqəsi yoxdur. Ayrı vaxtlarda alınan fərqli snapshot-lar yenə də qısa uyğunsuzluq yarada bilər.

## Sınaq variantları

- `off`: əvvəlki saxlanılmış davranış; nəzarət.
- `attack`: yeni hücum mövqelənməsi və müşahidə edilən top-qazanma keçidi; köhnə müdafiə.
- `compact`: köhnə hücum, yığcam müdafiə, əsasən öz yarımızda təzyiq.
- `trigger`: köhnə hücum, yığcam müdafiə və şərtli press.
- `high`: köhnə hücum, daha yüksək press; yorğunluq və hesab riski nəzərə alınır.
- `complete`: yeni hücum + şərtli press + yerli əks-press.
- `wide`: complete, hücumda daha geniş çıxışlar.
- `pivot`: complete, geridən çıxışda daha dərin iki cinah dəstəyi və yüksək pivot.

Yalnız bir dəyişəni ayıran variantlar və bir neçə qaydanı birləşdirən variantlar ayrıca yoxlanır. Bu, hər xüsusiyyətin müstəqil faydasını tam ölçən faktor təcrübəsi deyil.

## Oxunan real futbol mənbələri

- [FIFA: orta blok və orta press](https://www.fifatrainingcentre.com/en/game/tournaments/fifa-futsal-world-cup/the-mid-block-and-mid-press.php): birgə yığcam hərəkət, qarşı cinahdan sığorta, top tərəfə sıxılma və təhlükəli pivotun nəzarəti. Biz bunları sadələşdirilmiş mövqe/markaj qaydalarına çevirdik.
- [FIFA: yüksək blok və yüksək press](https://www.fifatrainingcentre.com/en/game/tournaments/fifa-futsal-world-cup/the-high-block-and-high-press.php): tək top sahibinə qaçmaq kifayət etmir; çıxışlar və fiziki imkan da nəzərə alınmalıdır. Bizdə yüksək press məsafə, örtük və enerji ilə məhdudlaşdırılır.
- [FIFA: aşağı blokda press](https://www.fifatrainingcentre.com/en/practice/futsal/block-3/low-block-press.php): cinaha ötürmə təzyiq üçün şərait yarada bilər. Bizdə cinah siqnalı təklikdə hər oyunçunu pressə göndərmir.
- [FIFA: təzyiq altında geridən çıxmaq](https://www.fifatrainingcentre.com/en/practice/futsal/block-2/playing-out-from-the-back-under-pressure.php): genişlik və irəlidə əlaqə nöqtəsi. Məşqdəki məcburi ötürmə sayını matç qaydasına köçürmədik.
- [FIFA: hücumda genişlik](https://www.fifatrainingcentre.com/en/practice/futsal/block-2/using-width-to-create-space-in-attack.php): topsuz dəstək və açılan ötürmə xətləri. Bizdə geniş çıxışların alternativi ayrıca sınanır; bütün rotasiyalar tam modelləşdirilməyib.
- [FIFA: son zonada pivot](https://www.fifatrainingcentre.com/en/practice/futsal/block-2/playing-into-the-pivot-in-the-final-third.php): irəli ötürmə, pivot və onun ətrafına dəstək. Bədən oriyentasiyası/texniki fəndlər native əmr müqaviləsində olmadığı üçün əlavə edilməyib.
- [FIFA: əks-pressin hazırlanması](https://www.fifatrainingcentre.com/en/practice/elite-sessions/transition-to-defending/preparing-and-executing-counter-pressing.php): dərhal təzyiq mümkün deyilsə, mərkəzi və ötürmə xətlərini qorumaq. Bizdə qısa pəncərə və yerli say üstünlüyü şərti var.
- [FIFA: müdafiəyə qayıdış](https://www.fifatrainingcentre.com/en/game/tournaments/fifa-futsal-world-cup/recovery.php): top sahibini ləngidərək digərlərinə qapı tərəfə qayıtmaq üçün vaxt vermək. Hər vəziyyətdə birbaşa top qazanmaq yeganə məqsəd deyil.

İnsan futzalının fizika və qaydaları bu simulyatorla eyni deyil. Buradakı mənbələr yerli performansın sübutu sayılmır; nəticə yalnız tamamlanmış matçlardan çıxarılır. Ötürmə və zərbə mexanikası nəzarət variantındakı kimidir; uydurma zərbə dəqiqliyi, topa ilk toxunuş və ya rəqib modelinin daxili məlumatı əlavə edilməyib.
