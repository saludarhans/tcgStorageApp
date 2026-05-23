"""
Populate the sealed_catalog table with every known sealed product.

Usage:
    python3 seed_sealed_catalog.py               # add missing entries
    python3 seed_sealed_catalog.py --reset        # wipe and rebuild
    python3 seed_sealed_catalog.py --update-images # patch image_url + set_codes on existing rows
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('FLASK_APP', 'run.py')

from app import app, db
from app.models import SealedCatalog
from app.forms import ALL_SETS, shorten_set_name

# ─── Image helpers ────────────────────────────────────────────────────────────
_GH = 'https://raw.githubusercontent.com/1niceroli/ptcg-assets/main'

def _raw(code, fn):   return f'{_GH}/{code}/{fn}'
def logo(code):        return f'https://images.pokemontcg.io/{code}/logo.png'
def sc(code):          return f',{code},'      # comma-padded set_codes value


# ─── Booster-pack art lists ───────────────────────────────────────────────────
# Tuples: (filename_in_packshots_dir, display_name)
PACKSHOTS = {
    # ── XY era ──
    'xy1':  [('XY1_Booster_Xerneas.webp','Xerneas'),    ('XY1_Booster_Yveltal.webp','Yveltal'),
             ('XY1_Booster_Blastoise.webp','Blastoise'), ('XY1_Booster_Venusaur.webp','Venusaur')],
    'xy8':  [('XY8_Booster_Mewtwo_X.webp','Mega Mewtwo X'),('XY8_Booster_Mewtwo_Y.webp','Mega Mewtwo Y'),
             ('XY8_Booster_Houndoom.webp','Houndoom'),   ('XY8_Booster_Zoroark.webp','Zoroark')],
    'xy12': [('XY12_Booster_Charizard.webp','Charizard'),('XY12_Booster_Blastoise.webp','Blastoise'),
             ('XY12_Booster_Venusaur.webp','Venusaur'),  ('XY12_Booster_Raichu.webp','Raichu')],

    # ── Sun & Moon era ──
    'sm1':  [('SM1_Booster_Solgaleo.webp','Solgaleo'),  ('SM1_Booster_Lunala.webp','Lunala'),
             ('SM1_Booster_Decidueye.webp','Decidueye'), ('SM1_Booster_Incineroar.webp','Incineroar'),
             ('SM1_Booster_Primarina.webp','Primarina')],
    'sm2':  [('SM2_Booster_Kommo-o.webp','Kommo-o'),    ('SM2_Booster_Lycanroc.webp','Lycanroc'),
             ('SM2_Booster_Ninetales.webp','Ninetales'), ('SM2_Booster_Tapu_Koko.webp','Tapu Koko')],
    'sm3':  [('SM3_Booster_Ho-Oh.webp','Ho-Oh'),        ('SM3_Booster_Marshadow.webp','Marshadow'),
             ('SM3_Booster_Necrozma.webp','Necrozma'),   ('SM3_Booster_Tapu_Fini.webp','Tapu Fini')],
    'sm4':  [('SM4_Booster_Buzzwole.webp','Buzzwole'),  ('SM4_Booster_Guzzlord.webp','Guzzlord'),
             ('SM4_Booster_Kartana.webp','Kartana'),     ('SM4_Booster_Silvally.webp','Silvally')],
    'sm5':  [('SM5_Booster_Dusk_Mane_Necrozma.webp','Dusk Mane Necrozma'),
             ('SM5_Booster_Dawn_Wings_Necrozma.webp','Dawn Wings Necrozma'),
             ('SM5_Booster_Giratina.webp','Giratina'),   ('SM5_Booster_Leafeon.webp','Leafeon')],
    'sm6':  [('SM6_Booster_Greninja.webp','Greninja'),  ('SM6_Booster_Naganadel.webp','Naganadel'),
             ('SM6_Booster_Necrozma.webp','Necrozma'),   ('SM6_Booster_Zygarde.webp','Zygarde')],
    'sm7':  [('SM7_Booster_Rayquaza.webp','Rayquaza'),  ('SM7_Booster_Jirachi.webp','Jirachi'),
             ('SM7_Booster_Blaziken.webp','Blaziken'),   ('SM7_Booster_Stakataka.webp','Stakataka')],
    'sm8':  [('SM8_Booster_Lugia.webp','Lugia'),        ('SM8_Booster_Celebi.webp','Celebi'),
             ('SM8_Booster_Zeraora.webp','Zeraora'),     ('SM8_Booster_Blacephalon.webp','Blacephalon')],
    'sm9':  [('SM9_Booster_Pikachu_Zekrom.webp','Pikachu & Zekrom'),
             ('SM9_Booster_Gengar_Mimikyu.webp','Gengar & Mimikyu'),
             ('SM9_Booster_Eevee_Snorlax.webp','Eevee & Snorlax'),
             ('SM9_Booster_Venusaur_Celebi.webp','Venusaur & Celebi')],
    'sm10': [('SM10_Booster_Charizard_Reshiram.webp','Charizard & Reshiram'),
             ('SM10_Booster_Gardevoir_Sylveon.webp','Gardevoir & Sylveon'),
             ('SM10_Booster_Lucario_Melmetal.webp','Lucario & Melmetal'),
             ('SM10_Booster_Machamp_Marshadow.webp','Machamp & Marshadow')],
    'sm11': [('SM11_Booster_Mewtwo_Mew.webp','Mewtwo & Mew'),
             ('SM11_Booster_Espeon_Deoxys.webp','Espeon & Deoxys'),
             ('SM11_Booster_Umbreon_Darkrai.webp','Umbreon & Darkrai'),
             ('SM11_Booster_Garchomp_Giratina.webp','Garchomp & Giratina')],
    'sm12': [('SM12_Booster_Solgaleo_Lunala.webp','Solgaleo & Lunala'),
             ('SM12_Booster_Dialga_Palkia_Arceus.webp','Dialga, Palkia & Arceus'),
             ('SM12_Booster_Blastoise_Piplup.webp','Blastoise & Piplup'),
             ('SM12_Booster_Cleffa_Igglybuff_Togepi.webp','Cleffa, Igglybuff & Togepi')],
    'sm75': [('Dragon_Majesty_Booster_Charizard.webp','Charizard'),
             ('Dragon_Majesty_Booster_Dragonite.webp','Dragonite'),
             ('Dragon_Majesty_Booster_Reshiram.webp','Reshiram'),
             ('Dragon_Majesty_Booster_Salamence.webp','Salamence')],
    'sm115':[('Hidden_Fates_Booster_Charizard.webp','Charizard'),
             ('Hidden_Fates_Booster_Mewtwo.webp','Mewtwo'),
             ('Hidden_Fates_Booster_Mew.webp','Mew'),
             ('Hidden_Fates_Booster_Legendary_Birds.png','Legendary Birds')],

    # ── Sword & Shield era ──
    'swsh1': [('SWSH1_Booster_Zacian.webp','Zacian'),   ('SWSH1_Booster_Zamazenta.webp','Zamazenta'),
              ('SWSH1_Booster_Gigantamax_Lapras.webp','Gigantamax Lapras'),
              ('SWSH1_Booster_Gigantamax_Snorlax.webp','Gigantamax Snorlax')],
    'swsh2': [('Sword_Shield—Rebel_Clash_Booster_Rillaboom_VMAX.webp','Rillaboom VMAX'),
              ('Sword_Shield—Rebel_Clash_Booster_Cinderace_VMAX.webp','Cinderace VMAX'),
              ('Sword_Shield—Rebel_Clash_Booster_Inteleon_VMAX.webp','Inteleon VMAX'),
              ('Sword_Shield—Rebel_Clash_Booster_Toxtricity_VMAX.webp','Toxtricity VMAX')],
    'swsh3': [('SWSH3_Booster_Gigantamax_Charizard.webp','Gigantamax Charizard'),
              ('SWSH3_Booster_Eternamax_Eternatus.webp','Eternamax Eternatus'),
              ('SWSH3_Booster_Gigantamax_Centiskorch.webp','Gigantamax Centiskorch'),
              ('SWSH3_Booster_Gigantamax_Grimmsnarl.webp','Gigantamax Grimmsnarl')],
    'swsh4': [('SWSH4_Booster_Gigantamax_Pikachu.webp','Gigantamax Pikachu'),
              ('SWSH4_Booster_Zarude.webp','Zarude'),    ('SWSH4_Booster_Celebi.webp','Celebi'),
              ('SWSH4_Booster_Gigantamax_Orbeetle.webp','Gigantamax Orbeetle')],
    'swsh5': [('Pokemon_TCG_Sword_Shield—Battle_Styles_Booster_Wrap_Single_Strike_Urshifu.webp','Single Strike Urshifu'),
              ('Pokemon_TCG_Sword_Shield—Battle_Styles_Booster_Wrap_Rapid_Strike_Urshifu.webp','Rapid Strike Urshifu'),
              ('Pokemon_TCG_Sword_Shield—Battle_Styles_Booster_Wrap_Empoleon.webp','Empoleon'),
              ('Pokemon_TCG_Sword_Shield—Battle_Styles_Booster_Wrap_Tyranitar.webp','Tyranitar')],
    'swsh6': [('SWSH6_Booster_Ice_Rider_Calyrex_copy.webp','Ice Rider Calyrex'),
              ('SWSH6_Booster_Shadow_Rider_Calyrex_copy.webp','Shadow Rider Calyrex'),
              ('SWSH6_Booster_Galarian_Articuno_copy.webp','Galarian Articuno'),
              ('SWSH6_Booster_Galarian_Moltres_copy.webp','Galarian Moltres'),
              ('SWSH6_Booster_Galarian_Zapdos_copy.webp','Galarian Zapdos')],
    'swsh7': [('SWSH7_Booster_Rayquaza.webp','Rayquaza'), ('SWSH7_Booster_Umbreon.webp','Umbreon'),
              ('SWSH7_Booster_Sylveon.webp','Sylveon'),
              ('SWSH7_Booster_Gigantamax_Duraludon.webp','Gigantamax Duraludon')],
    'swsh8': [('SWSH8_Booster_Mew.webp','Mew'),          ('SWSH8_Booster_Genesect.webp','Genesect'),
              ('SWSH8_Booster_Gigantamax_Gengar.webp','Gigantamax Gengar'),
              ('SWSH8_Booster_Boltund.webp','Boltund')],
    'swsh9': [('Pokemon_TCG_Sword_Shield—Brilliant_Stars_Booster_Wrap_Arceus_VSTAR-2.webp','Arceus VSTAR'),
              ('Pokemon_TCG_Sword_Shield—Brilliant_Stars_Booster_Wrap_Charizard_VSTAR-2.webp','Charizard VSTAR'),
              ('Pokemon_TCG_Sword_Shield—Brilliant_Stars_Booster_Wrap_Shaymin_VSTAR-2.webp','Shaymin VSTAR'),
              ('Pokemon_TCG_Sword_Shield—Brilliant_Stars_Booster_Wrap_Whimsicott_VSTAR-2.webp','Whimsicott VSTAR')],
    'swsh10':[('SWSH10_Booster_Origin_Dialga.webp','Origin Forme Dialga'),
              ('SWSH10_Booster_Origin_Palkia.webp','Origin Forme Palkia'),
              ('SWSH10_Booster_Hisuian_Decidueye.webp','Hisuian Decidueye'),
              ('SWSH10_Booster_Hisuian_Samurott.webp','Hisuian Samurott'),
              ('SWSH10_Booster_Hisuian_Typhlosion.webp','Hisuian Typhlosion')],
    'swsh11':[('SWSH11_Booster_Origin_Forme_Giratina.webp','Origin Forme Giratina'),
              ('SWSH11_Booster_Hisuian_Zoroark.webp','Hisuian Zoroark'),
              ('SWSH11_Booster_Radiant_Gardevoir.webp','Radiant Gardevoir'),
              ('SWSH11_Booster_Enamorus.webp','Enamorus')],
    'swsh12':[('HRAkc04667.webp','Lugia'),('HRAkc04667-03.webp','Alolan Vulpix'),
              ('HRAkc04667-04.webp','Regidrago')],
    'swsh12pt5':[('Crown_Zenith_Booster.webp','Standard')],

    # ── Scarlet & Violet era ──
    'sv1':  [('SV1_pack_Koraidon.webp','Koraidon'),   ('SV1_pack_Miraidon.webp','Miraidon'),
             ('SV1_pack_Gyarados.webp','Gyarados'),   ('SV1_pack_Partners.webp','Partners')],
    'sv2':  [('SV2_Booster_Chien-Pao.webp','Chien-Pao'),
             ('SV2_Booster_Meowscarada.webp','Meowscarada'),
             ('SV2_Booster_Quaquaval.webp','Quaquaval'),
             ('SV2_Booster_Skeledirge.webp','Skeledirge'),
             ('SV2_Booster_Ting-Lu.webp','Ting-Lu')],
    'sv3':  [('SV3_Booster_Charizard.webp','Charizard'), ('SV3_Booster_Tyranitar.webp','Tyranitar'),
             ('SV3_Booster_Dragonite.webp','Dragonite'), ('SV3_Booster_Revavroom.webp','Revavroom')],
    'sv3pt5':[('151_Booster.webp','Standard')],
    'sv4':  [('SV4_Booster_Roaring_Moon.webp','Roaring Moon'),
             ('SV4_Booster_Iron_Valiant.webp','Iron Valiant'),
             ('SV4_Booster_Armarouge.webp','Armarouge'),
             ('SV4_Booster_Garchomp.webp','Garchomp')],
    'sv4pt5':[('Pokemon_TCG_Scarlet_Violet—Paldean_Fates_Booster_Wrap_Ceruledge.webp','Ceruledge'),
              ('Pokemon_TCG_Scarlet_Violet—Paldean_Fates_Booster_Wrap_Dondozo.webp','Dondozo'),
              ('Pokemon_TCG_Scarlet_Violet—Paldean_Fates_Booster_Wrap_Pikachu.webp','Pikachu'),
              ('Pokemon_TCG_Scarlet_Violet—Paldean_Fates_Booster_Wrap_Tinkaton.webp','Tinkaton')],
    'sv5':  [('SV5_Booster_Walking_Wake.webp','Walking Wake'),
             ('SV5_Booster_Iron_Leaves.webp','Iron Leaves'),
             ('SV5_Booster_Raging_Bolt.webp','Raging Bolt'),
             ('SV5_Booster_Iron_Crown.webp','Iron Crown')],
    'sv6':  [('SV6_Booster_Ogerpon.webp','Ogerpon'),   ('SV6_Booster_Dragapult.webp','Dragapult'),
             ('SV6_Booster_Sinistcha.webp','Sinistcha'), ('SV6_Booster_Ursaluna.webp','Ursaluna')],
    'sv6pt5':[('Pokemon_TCG_Scarlet_Violet—Shrouded_Fable_Booster_Wrap_Okidogi.webp','Okidogi'),
              ('Pokemon_TCG_Scarlet_Violet—Shrouded_Fable_Booster_Wrap_Munkidori.webp','Munkidori'),
              ('Pokemon_TCG_Scarlet_Violet—Shrouded_Fable_Booster_Wrap_Fezandipiti.webp','Fezandipiti'),
              ('Pokemon_TCG_Scarlet_Violet—Shrouded_Fable_Booster_Wrap_Pecharunt.webp','Pecharunt')],
    'sv7':  [('Pokemon_TCG_Scarlet_Violet—Stellar_Crown_Booster_Wrap_Terapagos.png','Terapagos'),
             ('Pokemon_TCG_Scarlet_Violet—Stellar_Crown_Booster_Wrap_Cinderace.png','Cinderace'),
             ('Pokemon_TCG_Scarlet_Violet—Stellar_Crown_Booster_Wrap_Lapras.png','Lapras'),
             ('Pokemon_TCG_Scarlet_Violet—Stellar_Crown_Booster_Wrap_Galvantula.png','Galvantula')],
    'sv8':  [('Pokemon_TCG_Scarlet_Violet—Surging_Sparks_Booster_Wrap_PikachuStellar.png','Pikachu (Stellar)'),
             ('Pokemon_TCG_Scarlet_Violet—Surging_Sparks_Booster_Wrap_Archaludon.png','Archaludon'),
             ('Pokemon_TCG_Scarlet_Violet—Surging_Sparks_Booster_Wrap_Latias.png','Latias'),
             ('Pokemon_TCG_Scarlet_Violet—Surging_Sparks_Booster_Wrap_Alolan_Exeggutor.png','Alolan Exeggutor')],
    'sv8pt5':[('Pokemon_TCG_Scarlet_Violet—Prismatic_Evolutions_Booster_Wrap_Eevee_and_Sylveon.png','Eevee & Sylveon'),
              ('Pokemon_TCG_Scarlet_Violet—Prismatic_Evolutions_Booster_Wrap_Espeon_and_Umbreon.png','Espeon & Umbreon'),
              ('Pokemon_TCG_Scarlet_Violet—Prismatic_Evolutions_Booster_Wrap_Leafeon_and_Glaceon.png','Leafeon & Glaceon'),
              ('Pokemon_TCG_Scarlet_Violet—Prismatic_Evolutions_Booster_Wrap_Vaporeon_Jolteon_Flareon.png','Vaporeon, Jolteon & Flareon')],
    'sv9':  [("Pokemon_TCG_Scarlet_Violet—Journey_Together_Booster_Wrap_Hop's_Zacian.png","Hop's Zacian"),
             ("Pokemon_TCG_Scarlet_Violet—Journey_Together_Booster_Wrap_Iono_s_Bellibolt.png","Iono's Bellibolt"),
             ("Pokemon_TCG_Scarlet_Violet—Journey_Together_Booster_Wrap_Lillie's_Clefairy.png","Lillie's Clefairy"),
             ("Pokemon_TCG_Scarlet_Violet—Journey_Together_Booster_Wrap_N's_Zoroark.png","N's Zoroark")],
    'sv10': [("Pokemon_TCG_Scarlet_Violet—Destined_Rivals_Booster_Wrap_Giovanni_s_Mewtwo.png","Giovanni's Mewtwo"),
             ("Pokemon_TCG_Scarlet_Violet—Destined_Rivals_Booster_Wrap_Cynthia_s_Garchomp.png","Cynthia's Garchomp"),
             ("Pokemon_TCG_Scarlet_Violet—Destined_Rivals_Booster_Wrap_Ethan_s_Ho-Oh.png","Ethan's Ho-Oh"),
             ("Pokemon_TCG_Scarlet_Violet—Destined_Rivals_Booster_Wrap_Team_Rocket.png","Team Rocket")],

    # ── Mega Evolution era ──
    'me1':  [('ME1_Booster_Mega_Lucario.png','Mega Lucario'),
             ('ME1_Booster_Mega_Gardevoir.png','Mega Gardevoir'),
             ('ME1_Booster_Mega_Venusaur.png','Mega Venusaur'),
             ('ME1_Booster_Mega_Kangaskhan.png','Mega Kangaskhan')],
    'me2':  [('ME2_Booster_Mega_Charizard_X.png','Mega Charizard X'),
             ('ME2_Booster_Mega_Gengar.png','Mega Gengar'),
             ('ME2_Booster_Mega_Heracross.png','Mega Heracross'),
             ('ME2_Booster_Mega_Lopunny.png','Mega Lopunny')],
    'me3':  [('Pokemon_TCG_Mega_Evolution—Perfect_Order_Booster_Wrap_Mega_Zygarde.png','Mega Zygarde'),
             ('Pokemon_TCG_Mega_Evolution—Perfect_Order_Booster_Wrap_Mega_Clefable.png','Mega Clefable'),
             ('Pokemon_TCG_Mega_Evolution—Perfect_Order_Booster_Wrap_Mega_Starmie.png','Mega Starmie'),
             ('Pokemon_TCG_Mega_Evolution—Perfect_Order_Booster_Wrap_Meowth.png','Meowth')],
    'me4':  [('Pokemon_TCG_Mega_Evolution—Chaos_Rising_Booster_Wrap_Mega_Greninja.png','Mega Greninja'),
             ('Pokemon_TCG_Mega_Evolution—Chaos_Rising_Booster_Wrap_Mega_Dragalge.png','Mega Dragalge'),
             ('Pokemon_TCG_Mega_Evolution—Chaos_Rising_Booster_Wrap_Mega_Floette.png','Mega Floette'),
             ('Pokemon_TCG_Mega_Evolution—Chaos_Rising_Booster_Wrap_Mega_Pyroar.png','Mega Pyroar')],
}


# ─── Mini-tin lists ───────────────────────────────────────────────────────────
# Tuples: (filename_stem_with_ext, display_name)
MINI_TINS = {
    'swsh1':  [('grookey.png','Grookey'),('scorbunny.png','Scorbunny'),
               ('sobble.png','Sobble'),  ('yamper.png','Yamper'),
               ('ponyta.png','Galarian Ponyta')],
    'swsh3':  [('dragapult.png','Dragapult'),('toxtricity.png','Toxtricity'),
               ('rapidash.png','Galarian Rapidash'),('sirfetchd.png',"Sirfetch'd"),
               ('linoon.png','Linoone')],
    'swsh8':  [('chimchar.png','Chimchar'),('munchlax.png','Munchlax'),
               ('piplup.png','Piplup'),  ('riolu.png','Riolu'),
               ('turtwig.png','Turtwig')],
    'swsh12pt5':[('leon.png','Leon'),('marnie.png','Marnie'),('hop.png','Hop'),
                 ('bede.png','Bede'),   ('sonia.png','Sonia')],
    'cel25':  [('gen1.png','Generation 1'),('gen2.png','Generation 2'),
               ('gen3.png','Generation 3'),('gen4.png','Generation 4'),
               ('gen5.png','Generation 5'),('gen6.png','Generation 6'),
               ('gen7.png','Generation 7'),('gen8.png','Generation 8')],
    'sv3pt5': [('alakazam.png','Alakazam'),('arcanine.png','Arcanine'),
               ('dragonite.png','Dragonite'),('electabuzz.png','Electabuzz'),
               ('gengar.png','Gengar'),  ('machamp.png','Machamp'),
               ('magneton.png','Magneton'),('meowth.png','Meowth'),
               ('scyther.png','Scyther'),('slowpoke.png','Slowpoke')],
    'sv8pt5': [('1.webp','Vaporeon'), ('2.webp','Jolteon'),  ('3.webp','Flareon'),
               ('4.webp','Espeon'),   ('5.webp','Umbreon'),  ('6.webp','Leafeon'),
               ('7.webp','Glaceon'),  ('8.webp','Sylveon')],
    'me2pt5': [('Pokemon_TCG_Mega_Evolution—Ascended_Heroes_Pikachu.png','Pikachu'),
               ('Pokemon_TCG_Mega_Evolution—Ascended_Heroes_Clefairy.png','Clefairy'),
               ('Pokemon_TCG_Mega_Evolution—Ascended_Heroes_Riolu.png','Riolu'),
               ('Pokemon_TCG_Mega_Evolution—Ascended_Heroes_Togepi.png','Togepi'),
               ('Pokemon_TCG_Mega_Evolution—Ascended_Heroes_Zorua.png','Zorua')],
}


# ─── Booster Box images ───────────────────────────────────────────────────────
# Only sets that actually sold a retail booster box (36- or 30-pack display).
# Special/subset sets (Hidden Fates, Shining Fates, Paldean Fates, Shrouded
# Fable, Prismatic Evolutions, Black Bolt, White Flare, etc.) did not have one.
_BB_SETS = [
    'xy1','xy2','xy3','xy4','xy5','xy6','xy7','xy8','xy9','xy10','xy11','xy12',
    'sm1','sm2','sm3','sm4','sm5','sm6','sm7','sm8','sm9','sm10','sm11','sm12',
    'swsh1','swsh2','swsh3','swsh4','swsh5','swsh6','swsh7','swsh8',
    'swsh9','swsh10','swsh11','swsh12','swsh12pt5',
    'cel25','pgo',
    'sv1','sv2','sv3','sv3pt5','sv4','sv5','sv6',
    'sv7','sv8','sv9','sv10',
    'me1','me2',
]

# Sets with NO standalone booster box (special/subset releases).
_NO_BOX_SETS = {
    'sm75',    # Dragon Majesty  – subset, no booster box
    'sm115',   # Hidden Fates   – subset, no booster box
    'swsh35',  # Champion's Path – subset, no booster box
    'swsh45',  # Shining Fates   – subset, no booster box
    'sv4pt5',  # Paldean Fates   – subset, no booster box
    'sv6pt5',  # Shrouded Fable  – subset, no booster box
    'sv8pt5',  # Prismatic Evolutions – subset, no booster box
    'rsv10pt5','zsv10pt5',  # White Flare / Black Bolt – dual-set, no booster box
}

# Sets with NO standard 3-pack blister.
_NO_BLISTER_SETS = {
    'sm75',    # Dragon Majesty  – no retail blister
    'sm115',   # Hidden Fates   – no retail blister
    'swsh35',  # Champion's Path – no retail blister
    'swsh45',  # Shining Fates   – no retail blister
    'rsv10pt5','zsv10pt5',  # White Flare / Black Bolt – no retail blister
}

# ─── Elite Trainer Box images ─────────────────────────────────────────────────
_ETB = {
    'sv1':'elite-trainer-box-svp-13.png',   'sv2':'elite-trainer-box-svp-27.png',
    'sv3':'elite-trainer-box-svp-44.png',   'sv3pt5':'elite-trainer-box-svp-51.png',
    'sv4':'elite-trainer-box.png',           'sv4pt5':'elite-trainer-box-svp-75.png',
    'sv5':'elite-trainer-box-svp-97.png',   'sv6':'elite-trainer-box-svp-123.png',
    'sv6pt5':'elite-trainer-box-svp-129.png','sv7':'elite-trainer-box-svp-141.png',
    'sv8':'elite-trainer-box-svp-159.png',  'sv8pt5':'elite-trainer-box-svp-173.png',
    'sv9':'elite-trainer-box-svp-189.png',  'sv10':'elite-trainer-box-svp-203.png',
    'swsh1':'elite-trainer-box.png', 'swsh2':'elite-trainer-box.png',
    'swsh3':'elite-trainer-box.png', 'swsh4':'elite-trainer-box.png',
    'swsh5':'elite-trainer-box.png', 'swsh6':'elite-trainer-box.png',
    'swsh7':'elite-trainer-box.png', 'swsh8':'elite-trainer-box.png',
    'swsh9':'elite-trainer-box.png', 'swsh10':'elite-trainer-box.png',
    'swsh11':'elite-trainer-box.png','swsh12':'elite-trainer-box.png',
    'swsh12pt5':'elite-trainer-box-swshp-SWSH291.png',
    'swsh35':'elite-trainer-box-swshp-SWSH050.png',
    'swsh45':'elite-trainer-box-swshp-SWSH087.png',
    'cel25':'elite-trainer-box-swshp-SWSH144.png',
    'pgo':'elite-trainer-box-swshp-SWSH229.png',
    'sm75':'elite-trainer-box-smp-SM125.png',
    'sm115':'elite-trainer-box-smp-SM210.png',
    'me1':'elite-trainer-box.png', 'me2':'elite-trainer-box-mep-22.png',
    'me2pt5':'elite-trainer-box.png', 'me3':'elite-trainer-box.png',
    'me4':'elite-trainer-box.png',
    **{f'sm{i}':'elite-trainer-box.png' for i in range(1,13)},
    **{f'xy{i}':'elite-trainer-box.png' for i in range(1,13)},
}

# ─── Blister Pack images ──────────────────────────────────────────────────────
_BLISTER = {
    'sv1':'triple-blister-svp-11.png',   'sv2':'triple-blister-svp-25.png',
    'sv3':'triple-blister-svp-42.png',   'sv4':'triple-blister-svp-63.png',
    'sv4pt5':'triple-blister-svp-69.png','sv5':'triple-blister-svp-95.png',
    'sv6':'triple-blister-svp-121.png',  'sv6pt5':'triple-blister-svp-149.png',
    'sv7':'triple-blister-svp-139.png',  'sv8':'triple-blister-svp-156.png',
    'sv8pt5':'triple-blister-svp-170.png','sv9':'triple-blister-svp-187.png',
    'sv10':'triple-blister-svp-201.png',
    'swsh1':'triple-blister-swshp-SWSH012.png',
    'swsh2':'triple-blister-swshp-SWSH028.png',
    'swsh3':'triple-blister-swshp-SWSH041.png',
    'swsh4':'triple-blister-swshp-SWSH072.png',
    'swsh5':'triple-blister-swshp-SWSH094.png',
    'swsh6':'triple-blister-swshp-SWSH118.png',
    'swsh7':'triple-blister-swshp-SWSH128.png',
    'swsh8':'triple-blister-swshp-SWSH174.png',
    'swsh9':'triple-blister-swshp-SWSH191.png',
    'swsh10':'triple-blister-swshp-SWSH211.png',
    'swsh11':'triple-blister-swshp-SWSH246.png',
    'swsh12':'triple-blister-swshp-SWSH176.png',
    'swsh12pt5':'triple-blister-swshp-SWSH277.png',
    'pgo':'triple-blister-swshp-SWSH231.png',
    'sm1':'triple-blister-smp-SM08.png',
    'sm4':'triple-blister-smp-SM54.png',
    'sm5':'triple-blister-sm2-21a.png',
    'sm6':'triple-blister-sm2-51a.png',
    'sm10':'triple-blister-smp-SM185.png',
    'xy1':'triple-blister.png',           'xy2':'triple-blister-bw10-49.png',
    'xy3':'poke_xy03_3pblist_trevenant.jpg','xy4':'poke_xy4_blister_3.jpg',
    'xy7':'triple-blister-xyp-XY58.png',  'xy8':'triple-blister.png',
    'xy9':'triple-blister.png',            'xy10':'triple-blister-xyp-XY137.png',
    'xy11':'triple-blister.png',           'xy12':'triple-blister-xyp-XY160.png',
    'me1':'triple-blister-mep-7.png',     'me2':'triple-blister-mep-20.png',
}

# ─── Named-product image overrides ───────────────────────────────────────────
_NAMED_IMG = {
    '151 Binder Collection':     _raw('sv3pt5','binder-collection.png'),
    '151 Booster Bundle':        _raw('sv3pt5','booster-bundle.png'),
    'Prismatic Evolutions Collector Chest':
                                 _raw('sv8pt5','binder-collection.png'),
    'Prismatic Evolutions Special Illustration Collection':
                                 _raw('sv8pt5','poster-collection.png'),
}


# ─── set_codes for cross-set products ────────────────────────────────────────
# Products that include packs/cards from multiple sets.
# Format: comma-padded ",code1,code2,"
# Key = exact product name.
_CROSS_SET_CODES = {
    # Celebrations came with swsh8 (Fusion Strike) packs in many products
    'Celebrations Ultra Premium Collection':        ',cel25,swsh8,',
    'Celebrations Collector Chest':                 ',cel25,swsh8,',
    'Celebrations Classic Collection':              ',cel25,swsh8,',
    'Celebrations Premium Figure Collection':       ',cel25,swsh8,',
    # Pokémon GO released alongside swsh11 (Lost Origin)
    'Pokemon GO Premium Collection Mewtwo':         ',pgo,swsh11,',
    'Pokemon GO Premium Collection Radiant Eevee':  ',pgo,swsh11,',
    'Pokemon GO Gift Box':                          ',pgo,swsh11,',
    # Black Bolt & White Flare shared products (2 packs from each set)
    'Unova Poster Collection':                      ',rsv10pt5,zsv10pt5,',
    'Unova Victini Illustration Collection':        ',rsv10pt5,zsv10pt5,',
    'Unova Mini Tin (Reshiram)':                    ',rsv10pt5,zsv10pt5,',
    'Unova Mini Tin (Zekrom)':                      ',rsv10pt5,zsv10pt5,',
    'Unova Mini Tin (Snivy)':                       ',rsv10pt5,zsv10pt5,',
    'Unova Mini Tin (Tepig)':                       ',rsv10pt5,zsv10pt5,',
    'Unova Mini Tin (Oshawott)':                    ',rsv10pt5,zsv10pt5,',
    'Unova Mini Tin (Kyurem)':                      ',rsv10pt5,zsv10pt5,',
    'Unova Mini Tin (Zorua)':                       ',rsv10pt5,zsv10pt5,',
    'Unova Mini Tin (Victini)':                     ',rsv10pt5,zsv10pt5,',
}


# ─── Helper ───────────────────────────────────────────────────────────────────
def era_for(code):
    if code.startswith('me'):                                            return 'me'
    if code.startswith('swsh') or code in ('cel25','pgo','sm75','sm115',
                                            'swsh35','swsh45'):         return 'swsh'
    if code.startswith('sv') or code.startswith('rsv') or \
       code.startswith('zsv'):                                           return 'sv'
    if code.startswith('sm'):                                            return 'sm'
    if code.startswith('xy'):                                            return 'xy'
    return 'other'

def _img(code, itype, name):
    if name in _NAMED_IMG:               return _NAMED_IMG[name]
    if itype == 'Booster Box' and code in _BB_SETS:
        return _raw(code, 'display.png')
    if itype == 'Elite Trainer Box' and code in _ETB:
        return _raw(code, _ETB[code])
    if itype == 'Blister Pack' and code in _BLISTER:
        return _raw(code, _BLISTER[code])
    return logo(code)

def _sc(code, name):
    """Return the comma-padded set_codes string for a product."""
    if name in _CROSS_SET_CODES:
        return _CROSS_SET_CODES[name]
    return sc(code)


# ─── Special standalone sets (not in ALL_SETS standard loop) ─────────────────
SPECIAL_SETS = [
    ('swsh35', "Champion's Path"),
    ('swsh45', 'Shining Fates'),
]

# ─── Extra products keyed by set code ────────────────────────────────────────
EXTRAS = {
    # ── XY era ──
    'xy1':  [('Kalos Starter Set','Collection Box')],
    'xy3':  [('Furious Fists Mega Blastoise Collection','Premium Collection')],
    'xy5':  [('M Rayquaza-EX Collection','Premium Collection'),
             ('M Diancie-EX Collection','Premium Collection')],
    'xy6':  [('M Rayquaza-EX Collection (Colorless)','Premium Collection')],
    'xy8':  [('BREAKthrough Mega Mewtwo Collection','Premium Collection')],
    'xy12': [('Evolutions Premium Collection','Premium Collection'),
             ('Pikachu Power Collection','Premium Collection')],

    # ── Sun & Moon era ──
    'sm1':  [('Sun & Moon Solgaleo/Lunala Premium Collection','Premium Collection')],
    'sm2':  [('Guardians Rising Super Premium Collection','Super Premium Collection')],
    'sm3':  [('Burning Shadows Super Premium Collection','Super Premium Collection')],
    'sm5':  [('Ultra Prism Premium Collection','Premium Collection')],
    'sm6':  [('Forbidden Light Premium Collection','Premium Collection')],
    'sm7':  [('Celestial Storm Premium Collection','Premium Collection')],
    'sm8':  [('Lost Thunder Premium Collection','Premium Collection')],
    'sm9':  [('Team Up Premium Collection','Premium Collection')],
    'sm10': [('Unbroken Bonds Premium Collection','Premium Collection'),
             ('Unbroken Bonds Super Premium Collection','Super Premium Collection')],
    'sm11': [('Unified Minds Premium Collection','Premium Collection')],
    'sm12': [('Cosmic Eclipse Premium Collection','Premium Collection')],

    # ── SWSH Special sets ──
    'swsh35':[('Champion\'s Path Pokémon Center ETB','Elite Trainer Box')],
    'swsh45':[('Shining Fates Shiny Premium Collection','Premium Collection'),
              ('Shining Fates Mad Party Pin Collection','Collection Box'),
              ('Shining Fates Mini Tin','Tin')],

    # ── Sword & Shield era ──
    'swsh1': [('Sword & Shield Premium Collection','Premium Collection'),
              ('V Battle Deck Venusaur','Collection Box'),
              ('V Battle Deck Blastoise','Collection Box')],
    'swsh2': [('Rebel Clash Premium Collection','Premium Collection')],
    'swsh3': [('Darkness Ablaze Premium Collection','Premium Collection')],
    'swsh4': [('Vivid Voltage Premium Collection','Premium Collection'),
              ('Pikachu V Collection','Premium Collection')],
    'swsh5': [('Battle Styles Premium Collection','Premium Collection'),
              ('Single Strike Urshifu V Battle Deck','Collection Box'),
              ('Rapid Strike Urshifu V Battle Deck','Collection Box')],
    'swsh6': [('Chilling Reign Premium Collection','Premium Collection'),
              ('Calyrex VMAX Premium Collection','Super Premium Collection')],
    'swsh7': [('Evolving Skies Premium Collection','Premium Collection'),
              ('Rayquaza VMAX Premium Collection','Premium Collection'),
              ('Eevee Heroes Collector Chest','Collection Box')],
    'swsh8': [('Fusion Strike Premium Collection','Premium Collection'),
              ('Mew VMAX Premium Collection','Premium Collection')],
    'swsh9': [('Brilliant Stars Premium Collection','Premium Collection'),
              ('Charizard VSTAR Premium Collection','Premium Collection'),
              ('Arceus VSTAR Premium Collection','Premium Collection')],
    'swsh10':[('Astral Radiance Premium Collection','Premium Collection'),
              ('Hisuian Heavy Hitters Premium Collection','Premium Collection')],
    'swsh11':[('Lost Origin Premium Collection','Premium Collection'),
              ('Giratina VSTAR Premium Collection','Premium Collection')],
    'swsh12':[('Silver Tempest Premium Collection','Premium Collection'),
              ('Lugia VSTAR Premium Collection','Super Premium Collection')],
    'swsh12pt5':[
              ('Crown Zenith Galarian Gallery Premium Figure Collection','Premium Collection'),
              ('Crown Zenith Collector Chest','Collection Box'),
              ('Crown Zenith Tin Set','Tin')],
    'cel25': [('Celebrations Ultra Premium Collection','Super Premium Collection'),
              ('Celebrations Premium Figure Collection','Premium Collection'),
              ('Celebrations Classic Collection','Collection Box'),
              ('Celebrations Collector Chest','Collection Box'),
              ('Celebrations Mini Tin','Tin')],
    'pgo':   [('Pokemon GO Premium Collection Mewtwo','Premium Collection'),
              ('Pokemon GO Premium Collection Radiant Eevee','Premium Collection'),
              ('Pokemon GO Gift Box','Gift Box'),
              ('Pokemon GO Mini Tin','Tin')],

    # ── Scarlet & Violet era ──
    'sv1':   [('Scarlet & Violet Super Premium Collection','Super Premium Collection'),
              ('Miraidon ex Premium Collection','Premium Collection'),
              ('Koraidon ex Premium Collection','Premium Collection'),
              ('Scarlet & Violet Starter Set','Collection Box')],
    'sv2':   [('Paldea Evolved Premium Collection','Premium Collection')],
    'sv3':   [('Charizard ex Premium Collection','Premium Collection'),
              ('Obsidian Flames Collector Chest','Collection Box')],
    'sv3pt5':[('151 Premium 2-Pack Collection','Premium Collection'),
              ('151 Poster Collection','Collection Box'),
              ('151 Binder Collection','Collection Box'),
              ('151 Booster Bundle','Bundle')],
    'sv4':   [('Walking Wake ex Premium Collection','Premium Collection'),
              ('Iron Leaves ex Premium Collection','Premium Collection'),
              ('Paradox Rift Collector Chest','Collection Box')],
    'sv4pt5':[('Shiny Treasure ex Super Premium Collection','Super Premium Collection'),
              ('Paldean Fates Shiny Box','Collection Box')],
    'sv5':   [('Temporal Forces Premium Collection','Premium Collection'),
              ('Iron Crown ex Premium Collection','Premium Collection')],
    'sv6':   [('Twilight Masquerade Premium Collection','Premium Collection'),
              ('Ogerpon ex Premium Collection','Premium Collection')],
    'sv6pt5':[('Shrouded Fable Premium Collection','Premium Collection'),
              ('Bloodmoon Ursaluna ex Premium Collection','Premium Collection'),
              ('Shrouded Fable Booster Bundle','Bundle')],
    'sv7':   [('Stellar Crown Premium Collection','Premium Collection'),
              ('Stellar Crown Collector Chest','Collection Box')],
    'sv8':   [('Pikachu Ultra Premium Collection','Super Premium Collection'),
              ('Surging Sparks Collector Chest','Collection Box')],
    'sv8pt5':[('Pikachu Super Premium Collection','Super Premium Collection'),
              ('Prismatic Evolutions Collector Chest','Collection Box'),
              ('Prismatic Evolutions Special Illustration Collection','Collection Box'),
              ('Prismatic Evolutions Poster Collection','Collection Box'),
              ('Prismatic Evolutions Binder Collection','Collection Box'),
              ('Prismatic Evolutions Booster Bundle','Bundle')],
    'sv9':   [('Journey Together Super Premium Collection','Super Premium Collection'),
              ('Journey Together Premium Collection','Premium Collection'),
              ('Journey Together Booster Bundle','Bundle')],
    'sv10':  [('Destined Rivals Premium Collection','Premium Collection'),
              ('Destined Rivals Booster Bundle','Bundle')],

    # ── Mega Evolution era ──
    'me1':   [('Mega Evolution Premium Collection','Premium Collection')],
    'me2':   [('Phantasmal Flames Premium Collection','Premium Collection')],
    'me2pt5':[('Ascended Heroes Super Premium Collection','Super Premium Collection')],
    'me3':   [('Perfect Order Premium Collection','Premium Collection')],
    'me4':   [('Chaos Rising Premium Collection','Premium Collection')],
    # White Flare (rsv10pt5) — set-specific products
    'rsv10pt5':[('White Flare Booster Bundle','Bundle'),
                ('White Flare Binder Collection','Collection Box'),
                # Shared cross-set products (contain packs from BOTH sets):
                ('Unova Poster Collection','Collection Box'),
                ('Unova Victini Illustration Collection','Premium Collection'),
                ('Unova Mini Tin (Reshiram)','Tin'),
                ('Unova Mini Tin (Zekrom)','Tin'),
                ('Unova Mini Tin (Snivy)','Tin'),
                ('Unova Mini Tin (Tepig)','Tin'),
                ('Unova Mini Tin (Oshawott)','Tin'),
                ('Unova Mini Tin (Kyurem)','Tin'),
                ('Unova Mini Tin (Zorua)','Tin'),
                ('Unova Mini Tin (Victini)','Tin')],
    # Black Bolt (zsv10pt5) — set-specific products only
    'zsv10pt5':[('Black Bolt Booster Bundle','Bundle'),
                ('Black Bolt Binder Collection','Collection Box')],
}


# ─── Standard product types per era ──────────────────────────────────────────
# (name_suffix, item_type)  — booster packs are handled separately via PACKSHOTS
STANDARD = {
    'xy':   [('Booster Box','Booster Box'),
             ('Elite Trainer Box','Elite Trainer Box'),
             ('3-Pack Blister','Blister Pack')],
    'sm':   [('Booster Box','Booster Box'),
             ('Elite Trainer Box','Elite Trainer Box'),
             ('3-Pack Blister','Blister Pack')],
    'swsh': [('Booster Box','Booster Box'),
             ('Elite Trainer Box','Elite Trainer Box'),
             ('3-Pack Blister','Blister Pack')],
             # Mini Tin: only certain SWSH sets had them — handled via MINI_TINS/EXTRAS
    'sv':   [('Booster Box','Booster Box'),
             ('Elite Trainer Box','Elite Trainer Box'),
             ('3-Pack Blister','Blister Pack')],
    'me':   [('Booster Box','Booster Box'),
             ('Elite Trainer Box','Elite Trainer Box'),
             ('3-Pack Blister','Blister Pack')],
}


# ─── Build ────────────────────────────────────────────────────────────────────
def _row(name, itype, set_name, code, img=None, codes=None):
    return dict(
        name=name, item_type=itype,
        set_name=set_name, set_code=code,
        image_url=img or logo(code),
        set_codes=codes or sc(code),
    )

def build_products():
    rows = []
    all_set_codes = {code for code, _ in ALL_SETS}

    # Build set_name lookup
    set_names = {}
    for code, full_label in ALL_SETS:
        set_names[code] = shorten_set_name(full_label)

    # Add special sets not in ALL_SETS
    for code, full_label in SPECIAL_SETS:
        set_names[code] = shorten_set_name(full_label)

    def add_set(code, short):
        era = era_for(code)

        # 1. Booster pack arts (one entry per art)
        if code in PACKSHOTS:
            for fn, art in PACKSHOTS[code]:
                rows.append(_row(
                    f'{short} Booster Pack ({art})', 'Booster Pack', short, code,
                    img=_raw(code, f'packshots/{fn}'),
                ))
        else:
            rows.append(_row(f'{short} Booster Pack', 'Booster Pack', short, code))

        # 2. Standard products (box, ETB, blister)
        for suffix, itype in STANDARD.get(era, STANDARD['sv']):
            # Skip generic Mini Tin if we have individual tin art entries for this set
            if itype == 'Tin' and code in MINI_TINS:
                continue
            # Skip Booster Box for special/subset sets that never had one
            if itype == 'Booster Box' and code in _NO_BOX_SETS:
                continue
            # Skip 3-Pack Blister for sets that didn't have one
            if itype == 'Blister Pack' and code in _NO_BLISTER_SETS:
                continue
            name = f'{short} {suffix}'
            rows.append(_row(name, itype, short, code, img=_img(code, itype, name)))

        # 3. Mini tins (individual entries)
        if code in MINI_TINS:
            for fn, display in MINI_TINS[code]:
                name = f'{short} Mini Tin ({display})'
                rows.append(_row(name, 'Tin', short, code,
                                 img=_raw(code, f'mini-tins/{fn}')))

        # 4. Extra/specialty products
        for full_name, itype in EXTRAS.get(code, []):
            rows.append(_row(full_name, itype, short, code,
                             img=_img(code, itype, full_name),
                             codes=_sc(code, full_name)))

    # Main sets from ALL_SETS
    for code, _ in ALL_SETS:
        add_set(code, set_names[code])

    # Special sets
    for code, _ in SPECIAL_SETS:
        add_set(code, set_names[code])

    # Keep only the three catalog types — everything else is user-added
    allowed = {'Booster Pack', 'Elite Trainer Box', 'Super Premium Collection'}
    return [r for r in rows if r['item_type'] in allowed]


# ─── Seed / update ────────────────────────────────────────────────────────────
def run(reset=False, update_images=False):
    with app.app_context():
        if reset:
            SealedCatalog.query.delete()
            db.session.commit()
            print('Catalog cleared.')

        products = build_products()

        if update_images:
            updated = 0
            by_key = {(p['set_code'], p['name']): p for p in products}
            for row in SealedCatalog.query.all():
                p = by_key.get((row.set_code, row.name))
                if p:
                    changed = False
                    if row.image_url != p['image_url']:
                        row.image_url = p['image_url']; changed = True
                    if row.set_codes != p['set_codes']:
                        row.set_codes = p['set_codes'];  changed = True
                    if changed: updated += 1
                else:
                    # Fallback: recompute from set_code + item_type
                    new_url = _img(row.set_code or '', row.item_type or '', row.name)
                    new_sc  = _sc(row.set_code or '', row.name)
                    if row.image_url != new_url or row.set_codes != new_sc:
                        row.image_url = new_url; row.set_codes = new_sc; updated += 1
            db.session.commit()
            print(f'Updated {updated} rows.')
            return

        existing = {(r.set_code, r.name)
                    for r in SealedCatalog.query.with_entities(
                        SealedCatalog.set_code, SealedCatalog.name).all()}
        added = 0
        for p in products:
            if (p['set_code'], p['name']) not in existing:
                db.session.add(SealedCatalog(**p))
                added += 1
        db.session.commit()
        total = SealedCatalog.query.count()
        print(f'Added {added} products. Sealed catalog total: {total}.')


if __name__ == '__main__':
    run(
        reset='--reset' in sys.argv,
        update_images='--update-images' in sys.argv,
    )
