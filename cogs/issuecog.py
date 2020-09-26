import discord
from discord.ext import commands, tasks
from psutil import test
from sqlalchemy.orm.query import Query
import sqlalchemy
import hashlib
import json
from datetime import datetime
from time import time
from  sqlalchemy import Integer, String, Boolean, Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import Session, sessionmaker
Base=declarative_base()

class issues(commands.Cog):
    def __init__(self, bot:commands.Bot, dirname):
        self.dirname=dirname
        self.bot=bot
        self.engine=sqlalchemy.create_engine(f"sqlite:///{dirname}/test.db")
        self.Sessione=sessionmaker(bind=self.engine)
        self.session:Session=self.Sessione()
        self.trashman.start()


    @commands.before_invoke
    async def db_session(self,ctx):
        self.session=self.Sessione()
        
    @commands.after_invoke
    async def commit_afterwards(self,ctx):
        self.session.commit()
        self.session.close()

    @db_session
    @commit_afterwards
    @tasks.loop(minutes=10.0)
    async def trashman(self):
        self.dispose(self.session)

    class Issue(Base):
        __tablename__ = "issues"
        issue_id = Column(String,primary_key=True)
        timestamp = Column(Integer)
        author_id = Column(String)
        author_name = Column(String)
        message = Column(String)
        status = Column(String)
        hidden = Column(Boolean)
        disposable = Column(Boolean)

        def to_dict(self):
            return dict(
                issue_id=self.issue_id,
                timestamp=self.timestamp,
                author_id=int(self.author_id),
                author_name=self.author_name,
                message=self.message,
                status=self.status,
                hidden=self.hidden,
                disposable=self.disposable
                )

    class IssueStatus:
            Closed="closed"
            HighPriority="high priority"
            LowPriority="low priority"
            Open="open"
            InProgress="in progress"
            Frozen="frozen"

    def dispose(self,session:Session):
        trashbin=session.query(self.Issue).filter_by(disposable=True).all()
        for trash in trashbin:
            session.delete(trash)

    def close_issues(self,session:Session,issue_ids):
        if type(issue_ids) is str:
            issues=issue_ids.split(" ")
        elif type(issue_ids) is list:
            issues=issue_ids
        else:
            raise TypeError("this only works with strings (space seperated ids) or lists")
        print(issues)
        query:Query=session.query(self.Issue).filter(self.Issue.issue_id.in_(issues))
        to_close=query.all()
        for x in to_close:
            x.status=self.IssueStatus.Closed
            x.disposable=True

    def new_issue(self,session:Session,author_id:int,author_name:str,message:str,status:str="open",hidden:bool=False):
        nowtime=int(time())
        info=dict(
            timestamp=nowtime,
            author_id=author_id,
            author_name=author_name,
            message=message,
            status=status,
            hidden=hidden,
            disposable=False
            )
        print(info)
        issue_ids=hashlib.blake2b(json.dumps(info,sort_keys=True).encode(),digest_size=8).hexdigest()
        del info
        print(issue_ids)
        insert_issue=self.Issue(
            issue_id=issue_ids.lstrip().strip(),
            timestamp=nowtime,
            author_id=author_id,
            author_name=author_name.lstrip().strip(),
            message=message,
            status=status,
            hidden=hidden,
            disposable=False
            )
        session.add(insert_issue)
        return issue_ids

    @commands.group(name="issue")
    async def issue(self,ctx):
        pass

    @issue.command()
    @db_session
    @commit_afterwards
    async def new(self,ctx:commands.Context,*,message:str):
        id=ctx.message.author.id
        author_name=ctx.message.author.name
        message=message.lstrip().strip()
        issue_id=self.new_issue(self.session,id,author_name,message)
        await ctx.send(f"added new issue `{issue_id}`")

    @db_session
    @issue.command()
    async def get(self,ctx,id:str):
        id=id.strip().rstrip()
        issue=self.session.query(self.Issue).filter_by(issue_id=id).first()
        issue_dict:dict=issue.to_dict()
        date=datetime.fromtimestamp(issue_dict.get("timestamp"))
        embed=discord.Embed(title=f"issue {issue_dict.get('issue_id')}:")
        embed.add_field(name="date of creation",value=f"`{date}`",inline=True)
        embed.add_field(name="status",value=f"`{issue_dict.get('status')}`",inline=True)
        embed.add_field(name="author",value=f"`{issue_dict.get('author_id')}({issue_dict.get('author_name')})`",inline=True)
        embed.add_field(name="message",value=issue_dict.get("message"),inline=False)
        issue_dict.pop("issue_id")
        print(issue_dict)
        testhash=hashlib.blake2b(json.dumps(issue_dict,sort_keys=True).encode(),digest_size=8).hexdigest()
        if  testhash == id:
            embed.set_footer(text="integrity check passed.")
        else:
            embed.set_footer(text=f"WARNING INTEGRITY CHECK FAILED! HASH VALUES DON'T MATCH!!!\n**{testhash}** vs **{id}**")
        await ctx.send(embed=embed)

    @db_session
    @commit_afterwards
    @issue.command()
    async def close(self,ctx,*,ids):
        ids2=ids.strip().rstrip().split(" ")
        query:Query=self.session.query(self.Issue).filter(self.Issue.issue_id.in_(ids2))
        to_close=query.all()
        for x in to_close:
            x.status=self.IssueStatus.Closed
            x.disposable=True
        await ctx.send(f"closed {len(ids2)} issue(s): {ids}")



