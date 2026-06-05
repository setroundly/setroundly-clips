from build_patterns import build, GOLD, CREAM, AMBER

EMO   = "eq=saturation=0.80:brightness=-0.05:contrast=1.07,vignette=PI/4.2"
SONG  = "eq=saturation=1.05:contrast=1.03:gamma=1.02"
VIRAL = "eq=saturation=1.10:contrast=1.05:brightness=0.01"

# ---- caption banks (word-synced, from transcribed timings) ----
CH1 = [(72.12,74.12,"ハニーハニー"),(74.12,78.16,"«蜂蜜»みたいな"),(78.16,81.04,"まどろみにまみれても"),
       (81.04,84.22,"肌に残った«針»が"),(84.22,86.40,"チクチクしてる"),(86.40,90.50,"曖昧な匂いも")]
AITAI = [(230.62,233.44,"«幸せ»を探しても"),(233.44,235.38,"胸に残った"),(235.80,238.38,"過去には勝てないまま"),
         (238.64,242.00,"«会いたい»、心も"),(242.00,244.00,"身体も"),(244.54,247.50,"あの時と同じでも")]
MISE = [(125.78,130.48,"見せかけの"),(130.48,133.04,"優しさなんて"),(133.04,136.16,"本当に«要らない»"),
        (136.16,139.84,"あれこれと映し出す")]
HARI2 = [(192.0,194.28,"ハニーハニー"),(194.28,197.32,"«蜂蜜»みたいな"),(198.42,201.36,"まどろみにまみれても"),
         (201.36,203.88,"肌に残った"),(203.88,206.74,"«針»がチクチク"),(206.74,210.12,"曖昧においも")]
CO2 = [(776.42,779.00,"«歌うよ» 歌うよ 歌うよ"),(781.30,787.30,"このまま…"),(788.76,792.88,"このまま…")]
KASA = [(1623.26,1626.20,"悲しくないことを悲しまないで"),(1626.26,1629.08,"それはいつかの君が"),
        (1629.08,1632.46,"眠れない夜にこぼした"),(1632.46,1634.18,"«涙»でできた"),(1634.18,1639.40,"«透明な傘»があるから")]
MC = [(1454.18,1456.90,"今日みたいに晴れた日に"),(1457.90,1461.66,"懐かしい曲を流しながら走ってた"),
      (1473.60,1474.30,"音楽…"),(1474.74,1477.00,"大人になると聞けなくなる"),
      (1477.00,1479.48,"わかんないですか？"),(1481.26,1484.90,"昔みたいな«純粋»な気持ちで")]

S1 = [(72.10, 90.50)]      # 1st chorus (cx 736)
S2 = [(230.62, 247.50)]    # 会いたい (cx 656)
S3 = [(124.50, 139.90)]    # 見せかけの優しさ (cx 656)
S4 = [(192.00, 210.20)]    # 針 2nd chorus (cx 720)
S5 = [(776.40, 793.00)]    # CO2 歌うよ (cx 656)
S6 = [(1623.26, 1639.40)]  # tomorrow（歌詞: 透明な傘）(cx 656)
S7 = [(1454.18,1461.66),(1473.60,1479.50),(1481.26,1485.00)]  # MC 語り (cx 736)

BUG_HH = "♪ ハニーハニー / SETROUNDLY"
BUG_CO2 = "♪ CO2 / SETROUNDLY"
BUG_S = "SETROUNDLY"

def credit(text):
    return [(12.50, 9999, text)]

VIDEOS = [
 {"name":"b01_s1_emo","accent":CREAM,"cx":736,"segments":S1,"captions":CH1,"grade":EMO,
  "hooks":[(0.1,4.2,"全部どうでも\\Nよかった日に\\N\\Nできた«曲»。")],"bugs":credit(BUG_HH)},
 {"name":"b02_s1_viral","accent":AMBER,"cx":736,"segments":S1,"captions":CH1,"grade":VIRAL,
  "hooks":[(0.1,4.2,"«甘さ»だけ\\N探してた頃。")],"bugs":credit(BUG_HH)},
 {"name":"b03_s1_blackintro","accent":GOLD,"cx":736,"segments":S1,"captions":CH1,"grade":SONG,
  "intro":(1.6,"夜だけが\\N優しかった\\N\\N頃の曲。"),"hooks":[],"bugs":credit(BUG_HH)},
 {"name":"b04_s2_emo","accent":CREAM,"cx":656,"segments":S2,"captions":AITAI,"grade":EMO,
  "hooks":[(0.1,4.4,"«幸せ»を探しても\\N\\N過去には\\N勝てなかった。")],"bugs":credit(BUG_HH)},
 {"name":"b05_s2_blackintro","accent":AMBER,"cx":656,"segments":S2,"captions":AITAI,"grade":VIRAL,
  "intro":(1.6,"«会いたい»って\\N\\N言えなかった。"),"hooks":[],"bugs":credit(BUG_HH)},
 {"name":"b06_s2_song","accent":GOLD,"cx":656,"segments":S2,"captions":AITAI,"grade":SONG,
  "hooks":[(0.1,4.2,"心も身体も\\N\\Nまだ、«あの頃»。")],"bugs":credit(BUG_HH)},
 {"name":"b07_s3_emo","accent":CREAM,"cx":656,"segments":S3,"captions":MISE,"grade":EMO,
  "hooks":[(0.1,4.2,"«見せかけ»の\\N優しさは\\N\\Nいらなかった。")],"bugs":credit(BUG_HH)},
 {"name":"b08_s3_viral","accent":AMBER,"cx":656,"segments":S3,"captions":MISE,"grade":VIRAL,
  "hooks":[(0.1,4.0,"本当は\\N«いらなかった»。")],"bugs":credit(BUG_HH)},
 {"name":"b09_s4_emo","accent":CREAM,"cx":720,"segments":S4,"captions":HARI2,"grade":EMO,
  "hooks":[(0.1,4.2,"«蜂蜜»みたいに\\N\\N甘くて、痛い。")],"bugs":credit(BUG_HH)},
 {"name":"b10_s4_viral","accent":AMBER,"cx":720,"segments":S4,"captions":HARI2,"grade":VIRAL,
  "hooks":[(0.1,4.0,"肌に、\\Nまだ«残ってる»。")],"bugs":credit(BUG_HH)},
 {"name":"b11_s5_viral","accent":AMBER,"cx":656,"segments":S5,"captions":CO2,"grade":VIRAL,
  "hooks":[(0.1,4.2,"嘘は歌に\\N変えて、\\N\\N«歌うよ»。")],"bugs":credit(BUG_CO2)},
 {"name":"b12_s5_emo","accent":CREAM,"cx":656,"segments":S5,"captions":CO2,"grade":EMO,
  "hooks":[(0.1,4.2,"全部なくなっても\\N\\N残った«サビ»。")],"bugs":credit(BUG_CO2)},
 {"name":"b13_s5_song","accent":GOLD,"cx":656,"segments":S5,"captions":CO2,"grade":SONG,
  "hooks":[(0.1,4.0,"この«声»、\\N聴いてほしい。")],"bugs":credit(BUG_CO2)},
 {"name":"b14_s6_emo","accent":CREAM,"cx":656,"segments":S6,"captions":KASA,"grade":EMO,
  "hooks":[(0.1,4.4,"«眠れない夜»に\\N\\Nこぼした涙。")],"bugs":credit(BUG_S)},
 {"name":"b15_s6_viral","accent":AMBER,"cx":656,"segments":S6,"captions":KASA,"grade":VIRAL,
  "hooks":[(0.1,4.0,"この歌詞、\\N«やばい»。")],"bugs":credit(BUG_S)},
 {"name":"b16_s6_blackintro","accent":GOLD,"cx":656,"segments":S6,"captions":KASA,"grade":SONG,
  "intro":(1.6,"悲しくない\\Nことを\\N\\N«悲しまないで»。"),"hooks":[],"bugs":credit(BUG_S)},
 {"name":"b17_s7_emo","accent":CREAM,"cx":736,"segments":S7,"captions":MC,"grade":EMO,
  "hooks":[(0.1,4.2,"大人になると\\N\\N«純粋»に\\N聴けなくなる。")],"bugs":credit(BUG_S)},
 {"name":"b18_s7_viral","accent":AMBER,"cx":736,"segments":S7,"captions":MC,"grade":VIRAL,
  "hooks":[(0.1,4.0,"音楽、\\N«好き»でしたか？")],"bugs":credit(BUG_S)},
 {"name":"b19_s2_viral","accent":AMBER,"cx":656,"segments":S2,"captions":AITAI,"grade":VIRAL,
  "hooks":[(0.1,4.2,"どうでもよかった、\\N\\N«君以外»は。")],"bugs":credit(BUG_HH)},
 {"name":"b20_s1_blackintro","accent":GOLD,"cx":736,"segments":S1,"captions":CH1,"grade":SONG,
  "intro":(1.6,"«逃げ場所»が\\N欲しかった頃。"),"hooks":[],"bugs":credit(BUG_HH)},
]

if __name__ == "__main__":
    for i, s in enumerate(VIDEOS, 1):
        print(f"[{i}/{len(VIDEOS)}]", flush=True)
        build(s)
    print("ALL DONE", flush=True)
