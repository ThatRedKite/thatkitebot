import discord
from discord.ext import commands
from discord.ui import Select, View, Button
from discord.commands import Option

class InfoCog(commands.Cog, name="Info"):
    def __init__(self, bot):
        self.bot: discord.Bot = bot
        self.current_embed = None

        self.dropdown_view = None
        self.main_view = None

        self.buttons = [
            Button(
                emoji="⬅️",
                style= discord.ButtonStyle.gray,
                custom_id="prev"
            ),
            Button(
                emoji="➡️",
                style= discord.ButtonStyle.gray,
                custom_id="next",

            )
        ]

        for button in self.buttons: button.callback = self.button_callback

        # it doesn't accept emoji tags like :bulb:
        self.dropdown = Select(options=[
            discord.SelectOption(label="General Science", emoji="🔬"),
            discord.SelectOption(label="Chemistry", emoji="⚗️"),
            discord.SelectOption(label="Mathematics", emoji="🧮"),
            discord.SelectOption(label="Physics", emoji="🧲"),
            discord.SelectOption(label="Nature, Botany and Biology", emoji="🍀"),
            discord.SelectOption(label="Meteorology", emoji="⛈️"),
            discord.SelectOption(label="Astronomy and Rocketry", emoji="🔭"),
            discord.SelectOption(label="Geology and Geography", emoji="🌎"),
            discord.SelectOption(label="Engineering", emoji="🪛"),
            discord.SelectOption(label="Electronics", emoji="💡"),
            discord.SelectOption(label="Lasers", emoji="⛔"),
            discord.SelectOption(label="IT", emoji="💻"),
            ])
        self.dropdown.callback = self.dropdown_callback

        self.embeds = {
            "General Science": general_science_embed(),
            "Chemistry": chemistry_embed(),
            "Mathematics": mathematics_embed(),
            "Physics": physics_embed(),
            "Nature, Botany and Biology": biology_embed(),
            "Meteorology": meteorology_embed(),
            "Astronomy and Rocketry": astronomy_embed(),
            "Geology and Geography": geography_embed(),
            "Engineering": engineering_embed(),
            "Electronics": electronics_embed(),
            "Lasers": lasers_embed(),
            "IT": it_embed(),
        }

        # for auto-completion
        self.section_names = [
            "General Science",
            "Chemistry", 
            "Mathematics", 
            "Physics",
            "Nature, Botany and Biology",
            "Meteorology", 
            "Astronomy and Rocketry",
            "Geology and Geography",
            "Engineering", 
            "Electronics", 
            "Lasers", 
            "IT"
        ]


    async def get_sections(self, ctx: discord.AutocompleteContext):
        return [section for section in self.section_names if section.lower().startswith(ctx.value.lower())]


    @commands.slash_command(name="info")
    async def info(self, ctx, section: Option(str, "Pick a section!", required = False, autocomplete=get_sections) = None):
        """
        Sends YT channels, documents, books etc related to chosen science topic arranged in convenient way.
        """
        # setting up view for dropdown menu
        self.dropdown_view = View()
        self.dropdown_view.add_item(self.dropdown)

        # setting up view for embeds
        self.main_view = View()
        self.main_view.add_item(self.dropdown)
        for button in self.buttons: self.main_view.add_item(button)

        if section != None:
            try:
                await ctx.respond(embed=self.embeds[section], view=self.main_view)
            except:
                await ctx.respond("Incorrect section name!", delete_after=5.0)
        else:
            await ctx.respond("Choose a section!", view=self.dropdown_view)


    async def button_callback(self, interaction: discord.Interaction):
        if interaction.custom_id == "next":
            next = await self.get_next_embed()
            self.current_embed = next
            await interaction.response.edit_message(embed=next, view=self.main_view, content=None)
        else:
            prev = await self.get_previous_embed()
            self.current_embed = prev
            await interaction.response.edit_message(embed=prev, view=self.main_view, content=None)


    async def dropdown_callback(self, interaction: discord.Interaction):
        for key in self.embeds:
            if key in self.dropdown.values:
                self.current_embed = self.embeds[key]
                await interaction.response.edit_message(embed=self.embeds[key], view=self.main_view, content=None)
                break


    async def get_next_embed(self):
        next_embed = None
        arr = list(self.embeds.values())
        for i in range(len(arr)):
            if arr[i] == self.current_embed:
                try:
                    next_embed = arr[i+1]
                except:
                    next_embed = arr[0]

        return next_embed


    async def get_previous_embed(self):
        prev_embed = None
        arr = list(self.embeds.values())
        for i in range(len(arr)):
            if arr[i] == self.current_embed:
                try:
                    prev_embed = arr[i-1]
                except:
                    prev_embed = arr[len(arr)-1]
        
        return prev_embed


def general_science_embed():
    embed = discord.Embed(title = "General Science :microscope:", color = discord.Color.from_rgb(133, 193, 233))
    embed.add_field(
        name="Youtube", 
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
    embed = discord.Embed(title = "Chemistry :alembic:", color = discord.Color.blue())
    embed.add_field(
        name="Youtube", 
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
    embed = discord.Embed(title = "Mathematics :abacus:", color = discord.Color.dark_blue())
    embed.add_field(
        name="Youtube", 
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
    embed = discord.Embed(title = "Physics :magnet:", color = discord.Color.blurple())
    embed.add_field(
        name="Youtube", 
        value="""
            [Minute Physics](https://www.youtube.com/c/minutephysics)
            [Physics Fun](https://www.youtube.com/c/physicsfun)
            [ScienceClic English](https://www.youtube.com/c/ScienceClicEN)
            """
    )
    embed.add_field(
        name="Lectures",
        value="""
            Everything from mechanics to quantum-electrodynamics:
            [Feynman's general lectures](https://www.feynmanlectures.caltech.edu/messenger.html)   
            [The Feynman Lectures on Physics Volume I](https://www.feynmanlectures.caltech.edu/I_toc.html)
            [The Feynman Lectures on Physics Vol II](https://www.feynmanlectures.caltech.edu/II_toc.html)
            [The Feynman Lectures on Physics Vol III](https://www.feynmanlectures.caltech.edu/III_toc.html)
            """, inline=False
    )
    return embed


def biology_embed():
    embed = discord.Embed(title = "Nature, Botany and Biology :four_leaf_clover:", color = discord.Color.purple())
    embed.add_field(
        name="Youtube", 
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
    embed = discord.Embed(title = "Meteorology :thunder_cloud_rain:", color = discord.Color.brand_red())
    embed.add_field(
        name="Youtube",
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
    embed = discord.Embed(title = "Astronomy and Rocketry :telescope:", color = discord.Color.dark_red())
    embed.add_field(
        name="Youtube", 
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
    embed = discord.Embed(title = "Geology and Geography :earth_americas:", color = discord.Color.red())
    embed.add_field(
        name="Youtube",
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
    embed = discord.Embed(title = "Engineering :screwdriver:", color = discord.Color.orange())
    embed.add_field(
        name="Youtube", 
        value="""
            General:
            [MarcoReps](https://www.youtube.com/c/MarcoReps)
            [New Mind](https://www.youtube.com/c/NewMind)
            [Branch Education](https://www.youtube.com/c/BranchEducation)
            [Applied Science](https://www.youtube.com/c/AppliedScience)
            [Action BOX](https://www.youtube.com/c/ActionBOX)
            [Alpha Phoenix Channel](https://www.youtube.com/c/AlphaPhoenixChannel)
            [Nighthawkinlight](https://www.youtube.com/c/Nighthawkinlight)
            [Mark Rober](https://www.youtube.com/c/MarkRober)
            [James Bruton](https://www.youtube.com/c/jamesbruton)
            3D printing:
            [CNCKitchen](https://www.youtube.com/c/CNCKitchen)
            [SunShine](https://www.youtube.com/user/a09a21a)
            [Integza](https://www.youtube.com/c/Integza)
            [Teaching Tech](https://www.youtube.com/c/TeachingTech)
            [Chris Riley](https://www.youtube.com/c/ChrisRiley)
            """
    )
    embed.add_field(
        name="** **",
        value="""
            Theory:
            [The Efficient Engineer](https://www.youtube.com/c/TheEfficientEngineer)
            Good entertainment:
            [This Old Tony](https://www.youtube.com/c/ThisOldTony)
            [AvE](https://www.youtube.com/c/arduinoversusevil2025)
            Crazy projects:
            [Colinfurze](https://www.youtube.com/c/colinfurze)
            [The Thought Emporium](https://www.youtube.com/c/thethoughtemporium)
            [Stuff Made Here](https://www.youtube.com/c/StuffMadeHere)
            RC:
            [rctestflight](https://www.youtube.com/c/rctestflight)
            [RCLifeOn](https://www.youtube.com/c/RcLifeOn)
            [ProjectAir](https://www.youtube.com/c/ProjectAirAviation)
            Other:
            [MacPuffdog](https://youtube.com/user/MacPuffdog)
            """
    )
    return embed


def electronics_embed():
    embed = discord.Embed(title = "Electronics :bulb:", color = discord.Color.gold())
    embed.add_field(
        name="Youtube", 
        value="""
            If you want to start learning:
            [RSD Academy](https://www.youtube.com/c/RSDAcademy)
            [Leo's Bag of Tricks](https://www.youtube.com/channel/UCe1bjEcBichpiAMhExh0NiQ)
            [Element14](https://www.youtube.com/c/element14presents/)
            [The Offset Volt](https://www.youtube.com/c/TheOffsetVolt/)
            DIY projects with good explanations:
            [GreatScott!](https://www.youtube.com/c/greatscottlab)
            [Electronoobs](https://www.youtube.com/c/ELECTRONOOBS)
            [Bitluni](https://www.youtube.com/c/bitlunislab)
            [Elite Worm](https://www.youtube.com/c/EliteWorm)
            Good source of entertainment and education:
            [Electroboom](https://www.youtube.com/c/Electroboom/)
            [Big Clive](https://www.youtube.com/c/Bigclive)
            [DiodeGoneWild](https://www.youtube.com/c/DiodeGoneWild/)
            [Marco Reps](https://www.youtube.com/c/MarcoReps)
            [Afrotechmods](https://www.youtube.com/c/Afrotechmods)
            """
    )
    embed.add_field(
        name="** **",
        value="""
            Definitely worth your time:
            [Digi-Key](https://www.youtube.com/c/digikey)
            [EEVBlog](https://www.youtube.com/c/EevblogDave/)
            [Sam Ben-Yaakov](https://www.youtube.com/user/sambenyaakov)
            Embedded:
            [Jeff Geerling](https://www.youtube.com/c/JeffGeerling)
            [Mitch Davis](https://www.youtube.com/c/MitchDavis2/)
            Radio:
            [Charlie Morris](https://www.youtube.com/c/CharlieMorrisZL2CTM)
            [W2AEW](https://www.youtube.com/user/w2aew)
            [Mr Carlson's Lab](https://www.youtube.com/channel/UCU9SoQxJewrWb_3GxeteQPA)
            Others:
            [Keysight Labs](https://www.youtube.com/c/KeysightLabs)
            [Stephen Hawes](https://www.youtube.com/c/StephenHawesVideo)"""
    )
    embed.add_field(
        name="Free simulators, books, software, documents and useful websites",
        value="""
            [The Art of Electronics 3rd edition](https://cdn.discordapp.com/attachments/426054145645215756/783850352487170078/The_Art_of_Electronics_3rd_ed_2015.pdf)
            [Designing Electronics that Work](http://designingelectronics.com/#preview)
            [KiCad](https://www.kicad.org/)
            [Falstad](https://www.falstad.com/circuit/)
            [LTspice](https://www.analog.com/en/design-center/design-tools-and-calculators/ltspice-simulator.html)
            [SimulIDE](https://www.simulide.com/p/home.html)
            [All about circuits textbook](https://www.allaboutcircuits.com/textbook/)
            [Simon Bramble Designs and Tutorials](http://www.simonbramble.co.uk/index.htm)""", inline=False
    )
    
    embed.set_footer(text="Note: You should check out all of those YT channels")
    return embed


def lasers_embed():
    embed = discord.Embed(title = "Lasers :no_entry:", color = discord.Color.brand_green())
    embed.add_field(
        name="Youtube", 
        value="""
            [Zenodilodon](https://www.youtube.com/c/Zenodilodon)
            [LesLaboratory](https://www.youtube.com/c/LesLaboratory/)
            [Styropyro](https://www.youtube.com/c/styropyro)
            [Les' Lab](https://www.youtube.com/c/LesLaboratory)
            [Rocketman340](https://www.youtube.com/user/rocketman340)
            """
    )
    embed.add_field(
        name="Websites",
        value="""
            [Sam's Laser](https://www.repairfaq.org/sam/lasersam.htm)
        """, inline=False
    )

    return embed


def it_embed():
    embed = discord.Embed(title = "Computing and Programming :computer:", color = discord.Color.green())
    embed.add_field(
        name="Youtube", 
        value="""
            General:
            [Level1Techs](https://www.youtube.com/c/level1techs)
            Security:
            [LiveOverflow](https://www.youtube.com/c/LiveOverflow)
            [Sumsubcom](https://www.youtube.com/c/Sumsubcom)
            [Lawrence systems](https://www.youtube.com/channel/UCHkYOD-3fZbuGhwsADBd9ZQ)
            Repairs:
            [NorthridgeFix](https://www.youtube.com/c/NorthridgeFix)
            [Rossmanngroup](https://www.youtube.com/user/rossmanngroup)
            [SebastianLague](https://www.youtube.com/c/SebastianLague)
            [Code Parade](https://www.youtube.com/c/CodeParade)
            """
    )
    embed.add_field(
        name="** **",
        value="""
            Showcase:
            [Unboxtherapy](https://www.youtube.com/c/unboxtherapy)
            [Linus Tech Tips](https://www.youtube.com/c/LinusTechTips)
            [Mrkeybrd](https://www.youtube.com/c/Mrkeybrd)
        """
    )
    embed.add_field(
        name="Docs and Software", 
        value="""
            [Microsoft Docs](https://docs.microsoft.com/en-us/)
            [Grafana](https://grafana.com/docs/grafana/latest/)
            [Prometheus](https://prometheus.io/docs/introduction/overview/)
            [Docker](https://docs.docker.com/)
            [TLDP](https://tldp.org/)
            """, inline=False
    )
    
    return embed


def setup(bot):
    bot.add_cog(InfoCog(bot))
