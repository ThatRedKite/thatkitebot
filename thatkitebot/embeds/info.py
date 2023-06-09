#  Copyright (c) 2019-2023 ThatRedKite and contributors

from discord import Embed, Color


def general_science_embed():
    embed = Embed(title="General Science :microscope:", color=Color.from_rgb(133, 193, 233))
    embed.add_field(
        name="YouTube",
        value="""
            [Be Smart](https://www.youtube.com/c/itsokaytobesmart)
            [Brainiac](https://www.youtube.com/c/brainiac75)
            [CGP Grey](https://www.youtube.com/greymatter)
            [Cody's Lab](https://www.youtube.com/user/theCodyReeder)
            [Kurzgesagt – In a Nutshell](https://www.youtube.com/c/inanutshell)
            [QuantaScience](https://www.youtube.com/c/QuantaScienceChannel)
            [SciShow](https://www.youtube.com/c/SciShow)
            [Smarter every day](https://www.youtube.com/c/smartereveryday)
            [The Backyard Scientist](https://www.youtube.com/c/TheBackyardScientist)
            [Alpha Phoenix](https://www.youtube.com/c/AlphaPhoenixChannel)
            [Applied Science](https://www.youtube.com/c/AppliedScience)
            [Steve Mould](https://www.youtube.com/c/SteveMould)
                """
    )
    return embed


def chemistry_embed():
    embed = Embed(title="Chemistry :alembic:", color=Color.blue())
    embed.add_field(
        name="YouTube",
        value="""
            If you want to start learning:
            [Safety](https://www.youtube.com/watch?v=ftACSEJ6DZA)
            [Periodic Videos](https://www.youtube.com/user/periodicvideos)
            [Thoisoi2](https://www.youtube.com/channel/UC3j3w-oUtIAm_KI857ydvUA)
            [That Chemist](https://www.youtube.com/c/ThatChemist2)
            Good source of entertainment and education:
            [Cody's Lab](https://www.youtube.com/user/theCodyReede)
            [Styropyro](https://www.youtube.com/c/styropyro)
            [Chemiolis](https://www.youtube.com/c/Chemiolis)
            [Thy Labs](https://www.youtube.com/c/THYZOIDLABORATORIES)
            [Nile Red](https://www.youtube.com/c/NileRed)
            [Nile Blue](https://www.youtube.com/c/NileRed2)
            [ChemicalForce](https://www.youtube.com/c/ChemicalForce)
            """
    )
    embed.add_field(
        name="** **",
        value="""
            \"Home\" preps:
            [Scrap Science](https://www.youtube.com/c/ScrapScience)
            [DougsLab](https://www.youtube.com/user/DougsLab)
            [NurdRage](https://www.youtube.com/c/NurdRage)
            [Explosions&Fire](https://www.youtube.com/c/ExplosionsFire2)
            [Extractions&Ire](https://www.youtube.com/c/ExtractionsIre)
            [ChemPlayer](https://www.bitchute.com/channel/2vWmMgSEZ2jf/)
            [PoorMansChemist](https://www.bitchute.com/channel/CLgwoqXAHT7I/)
            [The Canadian Chemist](https://www.youtube.com/c/TheCanadianChemist/)
            [Elemental Maker](https://www.youtube.com/c/ElementalMaker)
        """
    )
    return embed


def mathematics_embed():
    embed = Embed(title="Mathematics :abacus:", color=Color.dark_blue())
    embed.add_field(
        name="YouTube",
        value="""
            [Stand-up Maths](https://www.youtube.com/c/MindYourDecisions)
            [MindYourDecisions](https://www.youtube.com/c/MindYourDecisions)
            [3Blue1Brown](https://www.youtube.com/c/3blue1brown)
            [Mathologer](https://www.youtube.com/c/Mathologer)
            [Mathematical Visual Proofs](https://www.youtube.com/c/MicroVisualProofs)
            """
    )
    return embed


def physics_embed():
    embed = Embed(title="Physics :magnet:", color=Color.blurple())
    embed.add_field(
        name="YouTube",
        value="""
            [Minute Physics](https://www.youtube.com/c/minutephysics)
            [Physics Fun](https://www.youtube.com/c/physicsfun)
            [ScienceClic English](https://www.youtube.com/c/ScienceClicEN)
            """
    )
    embed.add_field(
        name="Lectures",
        value="""
            Everything from Mechanics to Quantum-Electrodynamics:
            [Feynman's general lectures](https://www.feynmanlectures.caltech.edu/messenger.html)   
            [The Feynman Lectures on Physics Volume I](https://www.feynmanlectures.caltech.edu/I_toc.html)
            [The Feynman Lectures on Physics Volume II](https://www.feynmanlectures.caltech.edu/II_toc.html)
            [The Feynman Lectures on Physics Volume III](https://www.feynmanlectures.caltech.edu/III_toc.html)
            """, inline=False
    )
    return embed


def biology_embed():
    embed = Embed(title="Nature, Botany and Biology :four_leaf_clover:", color=Color.purple())
    embed.add_field(
        name="YouTube",
        value="""
            General:
            [Zefrank](https://www.youtube.com/c/zefrank)
            [Andrew Camarata](https://www.youtube.com/c/AndrewCamarata)
            [Robert E Fuller](https://youtube.com/c/RobertEFuller)
            Spiders:
            [Exotics Lair](https://www.youtube.com/c/ExoticsLair)
            Moths:
            [Bart Coppens](https://www.youtube.com/channel/UCurn5x0b5VqPvIuDohYiSaw)
            Survival:
            [Kent Survival](https://www.youtube.com/c/KentSurvival)
            Microbiology:
            [Journey to the Microcosmos](https://www.youtube.com/c/microcosmos)
            Jars:
            [Life in Jars](https://www.youtube.com/c/LifeinJars)
            [Jartopia](https://youtube.com/c/Jartopia)
            """
    )
    return embed


def meteorology_embed():
    embed = Embed(title="Meteorology :thunder_cloud_rain:", color=Color.brand_red())
    embed.add_field(
        name="YouTube",
        value="""
            [Skip Talbot Storm Chasing](https://www.youtube.com/c/skiptalbot)
            [Tornado Titans](https://www.youtube.com/c/tornadotitans)
            [NWSTrainingCenter](https://www.youtube.com/watch?v=6XgEsp6UMJo&list=PLYsC5TDceC_ZYXK9tpG0jJZ7rvLhFRDaO)
            [Guide to Sckew-Ts and Hodographs](https://www.youtube.com/playlist?list=PLnjboQ2ku8GDI9DGcqR8d9sr0sZKhH-qX)
            [Convective Chronicles](https://www.youtube.com/c/ConvectiveChronicles)
            """
    )
    return embed


def astronomy_embed():
    embed = Embed(title="Astronomy and Rocketry :telescope:", color=Color.dark_red())
    embed.add_field(
        name="YouTube",
        value="""
            [Primal Space](https://www.youtube.com/channel/UClZbmi9JzfnB2CEb0fG8iew)
            [BPS space](https://www.youtube.com/c/BPSspace)
            [AstroBackyard](https://www.youtube.com/c/AstroBackyard)
            [Everyday Astronaut](https://www.youtube.com/c/EverydayAstronaut)
            [Scott Manley](https://www.youtube.com/c/szyzyg)
            [Dr. Becky ](https://www.youtube.com/channel/UCYNbYGl89UUowy8oXkipC-Q)
            """
    )
    embed.add_field(
        name="Books",
        value="""
            [An Introduction to Modern Astrophysics](https://www.academia.edu/42881683/An_Introduction_to_Modern_Astrophysics)
            [Turn Left at Orion](https://www.pdfdrive.com/turn-left-at-orion-a-hundred-night-sky-objects-to-see-in-a-small-telescope-and-how-to-find-them-e175402242.html)
            The Dobsonian Telescope - David Kriege, Richard Berry
            """
    )
    return embed


def geography_embed():
    embed = Embed(title="Geology and Geography :earth_americas:", color=Color.red())
    embed.add_field(
        name="YouTube",
        value="""
            [Cody's Lab](https://www.youtube.com/user/theCodyReeder)
            [hugefloods](https://www.youtube.com/user/hugefloods)
        """
    )
    embed.add_field(
        name="Websites",
        value="""
            [GIA](https://www.gia.edu/gem-education/overview)
            [Minerals](https://www.mindat.org/)
            [USGS geologic maps](https://ngmdb.usgs.gov/ngmdb/ngmdb_home.html)
        """
    )
    return embed


def engineering_embed():
    embed = Embed(title="Engineering :screwdriver:", color=Color.orange())
    embed.add_field(
        name="YouTube",
        value=("General:\n"
               "[MarcoReps](https://www.youtube.com/c/MarcoReps)\n"
               "[New Mind](https://www.youtube.com/c/NewMind)\n"
               "[Branch Education](https://www.youtube.com/c/BranchEducation)\n"
               "[Applied Science](https://www.youtube.com/c/AppliedScience)\n"
               "[Action BOX](https://www.youtube.com/c/ActionBOX)\n"
               "[Alpha Phoenix Channel](https://www.youtube.com/c/AlphaPhoenixChannel)\n"
               "[Nighthawkinlight](https://www.youtube.com/c/Nighthawkinlight)\n"
               "[Mark Rober](https://www.youtube.com/c/MarkRober)\n"
               "[James Bruton](https://www.youtube.com/c/jamesbruton)\n"
               "3D printing:\n"
               "[CNCKitchen](https://www.youtube.com/c/CNCKitchen)\n"
               "[SunShine](https://www.youtube.com/user/a09a21a)\n"
               "[Integza](https://www.youtube.com/c/Integza)\n"
               "[Teaching Tech](https://www.youtube.com/c/TeachingTech)\n"
               "[Chris Riley](https://www.youtube.com/c/ChrisRiley)\n"
               )
    )
    embed.add_field(
        name="** **",
        value=("Theory:\n"
               "[The Efficient Engineer](https://www.youtube.com/c/TheEfficientEngineer)\n"
               "Good entertainment:\n"
               "[This Old Tony](https://www.youtube.com/c/ThisOldTony)\n"
               "[AvE](https://www.youtube.com/c/arduinoversusevil2025)\n"
               "Crazy projects:\n"
               "[Colinfurze](https://www.youtube.com/c/colinfurze)\n"
               "[The Thought Emporium](https://www.youtube.com/c/thethoughtemporium)\n"
               "[Stuff Made Here](https://www.youtube.com/c/StuffMadeHere)\n"
               "RC:\n"
               "[rctestflight](https://www.youtube.com/c/rctestflight)\n"
               "[RCLifeOn](https://www.youtube.com/c/RcLifeOn)\n"
               "[ProjectAir](https://www.youtube.com/c/ProjectAirAviation)\n"
               "Other:\n"
               "[MacPuffdog](https://youtube.com/user/MacPuffdog)\n"
               )
    )
    return embed


def electronics_embed():
    embed = Embed(title="Electronics :bulb:", color=Color.gold())
    embed.add_field(
        name="YouTube",
        value=("If you want to start learning:\n"
               "[RSD Academy](https://www.youtube.com/c/RSDAcademy)\n"
               "[Leo's Bag of Tricks](https://www.youtube.com/channel/UCe1bjEcBichpiAMhExh0NiQ)\n"
               "[Element14](https://www.youtube.com/c/element14presents/)\n"
               "[The Offset Volt](https://www.youtube.com/c/TheOffsetVolt/)\n"
               "DIY projects with good explanations:\n"
               "[GreatScott!](https://www.youtube.com/c/greatscottlab)\n"
               "[Electronoobs](https://www.youtube.com/c/ELECTRONOOBS)\n"
               "[Bitluni](https://www.youtube.com/c/bitlunislab)\n"
               "[Elite Worm](https://www.youtube.com/c/EliteWorm)\n"
               "Good source of entertainment and education:\n"
               "[Electroboom](https://www.youtube.com/c/Electroboom/)\n"
               "[Big Clive](https://www.youtube.com/c/Bigclive)\n"
               "[DiodeGoneWild](https://www.youtube.com/c/DiodeGoneWild/)\n"
               "[Marco Reps](https://www.youtube.com/c/MarcoReps)\n"
               "[Afrotechmods](https://www.youtube.com/c/Afrotechmods)\n"
               )
    )
    embed.add_field(
        name="** **",
        value=("Definitely worth your time:\n"
               "[Digi-Key](https://www.youtube.com/c/digikey)\n"
               "[EEVBlog](https://www.youtube.com/c/EevblogDave/)\n"
               "[Sam Ben-Yaakov](https://www.youtube.com/user/sambenyaakov)\n"
               "Embedded:\n"
               "[Jeff Geerling](https://www.youtube.com/c/JeffGeerling)\n"
               "[Mitch Davis](https://www.youtube.com/c/MitchDavis2/)\n"
               "Radio:\n"
               "[Charlie Morris](https://www.youtube.com/c/CharlieMorrisZL2CTM)\n"
               "[W2AEW](https://www.youtube.com/user/w2aew)\n"
               "[Mr Carlson's Lab](https://www.youtube.com/channel/UCU9SoQxJewrWb_3GxeteQPA)\n"
               "Others:\n"
               "[Keysight Labs](https://www.youtube.com/c/KeysightLabs)\n"
               "[Stephen Hawes](https://www.youtube.com/c/StephenHawesVideo)"
                ),
    )
    embed.add_field(
        name="Free simulators, books, software, documents and useful websites",
        value=("[The Art of Electronics 3rd edition](https://cdn.discordapp.com/attachments/426054145645215756/783850352487170078/The_Art_of_Electronics_3rd_ed_2015.pdf)\n"
               "[Designing Electronics that Work](http://designingelectronics.com/#preview)\n"
               "[KiCad](https://www.kicad.org/)\n"
               "[Falstad](https://www.falstad.com/circuit/)\n"
               "[LTspice](https://www.analog.com/en/design-center/design-tools-and-calculators/ltspice-simulator.html)\n"
               "[SimulIDE](https://www.simulide.com/p/home.html)\n"
               "[All About Circuits Textbook](https://www.allaboutcircuits.com/textbook/)\n"
               "[Simon Bramble Designs and Tutorials](http://www.simonbramble.co.uk/index.htm)"
               ),
    )

    embed.set_footer(text="Note: You should check out all of those YT channels")
    return embed


def lasers_embed():
    embed = Embed(title="Lasers :no_entry:", color=Color.brand_green())
    embed.add_field(
        name="YouTube",
        value=("[Zenodilodon](https://www.youtube.com/c/Zenodilodon)\n"
               "[LesLaboratory](https://www.youtube.com/c/LesLaboratory/)\n"
               "[Styropyro](https://www.youtube.com/c/styropyro)\n"
               "[Les' Lab](https://www.youtube.com/c/LesLaboratory)\n"
               "[Rocketman340](https://www.youtube.com/user/rocketman340)\n"
               )
    )
    
    embed.add_field(
        name="Websites",
        value=("[Sam's Laser](https://www.repairfaq.org/sam/lasersam.htm)\n"
               )
    )

    return embed


def it_embed():
    embed = Embed(title="Computing and Programming :computer:", color=Color.green())
    embed.add_field(
        name="YouTube",
        value=("General:\n"
               "[Level1Techs](https://www.youtube.com/c/level1techs)\n"
               "Security:\n"
               "[LiveOverflow](https://www.youtube.com/c/LiveOverflow)\n"
               "[Sumsubcom](https://www.youtube.com/c/Sumsubcom)\n"
               "[Lawrence systems](https://www.youtube.com/channel/UCHkYOD-3fZbuGhwsADBd9ZQ)\n"
               "Repairs:\n"
               "[NorthridgeFix](https://www.youtube.com/c/NorthridgeFix)\n"
               "[Rossmanngroup](https://www.youtube.com/user/rossmanngroup)\n"
               "[SebastianLague](https://www.youtube.com/c/SebastianLague)\n"
               "[Code Parade](https://www.youtube.com/c/CodeParade)\n"
               )
        
    )
    embed.add_field(
        name="** **",
        value=("Showcase:\n"
               "[Unboxtherapy](https://www.youtube.com/c/unboxtherapy)\n"
               "[Linus Tech Tips](https://www.youtube.com/c/LinusTechTips)\n"
               "[Mrkeybrd](https://www.youtube.com/c/Mrkeybrd)\n"
               )
    )
    embed.add_field(
        name="Docs and Software",
        value=("[Microsoft Docs](https://docs.microsoft.com/en-us/)\n"
               "[Grafana](https://grafana.com/docs/grafana/latest/)\n"
               "[Prometheus](https://prometheus.io/docs/introduction/overview/)\n"
               "[Docker](https://docs.docker.com/)\n"
               "[TLDP](https://tldp.org/)\n"
               ),
        inline=False
    )

    return embed
