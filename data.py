import os, time, json, string, re, random, threading, traceback, sys
import livejson, requests

class commands(threading.Thread):
    def __init__(self, fileName, client, app, uid):
        super(commands, self).__init__()
        self.fileName = fileName
        self.client = client
        self.app = app
        self.uid = uid
        self.db = livejson.File("database/%s.json"%fileName, True, True, 4)
        self.master = ["YOUR_MID"]
        self.invites = []
        self.settings = {
            "protect": {},
            "namelock": {},
            "linkprotect": {},
            "denyinvite": {},
            "autopurge": False,
            "allowban": True,
            "sqmode": False,
            "rname": fileName,
            "sname": "default"
        }
        if not "settings" in self.db:
            self.db['settings'] = self.settings
            self.settings = self.db["settings"]
            for oup in self.master:
                client.sendMessage(oup,"I'm just created.\nMy uid: %s"%uid)
        else:
            self.settings = self.db["settings"]
        self.stats = {
            "owners": [],
            "admins": [],
            "staffs": [],
            "bots": [],
            "antijs": [],
            "banned": []
        }
        if not "stats" in self.db:
            self.db['stats'] = self.stats
            self.stats = self.db["stats"]
        else:
            self.stats = self.db["stats"]

    def banned(self, user):
        if user in self.stats["banned"] or not self.settings["allowban"]:pass
        else:self.stats["banned"].append(user)
        return 1

    def canceling(self, to, target):
        for a in target:
            try:self.client.cancelGroupInvitation(to, [a])
            except:e = traceback.format_exc()

    def mycmd(self, text, rname, sname):
        cmd = ""
        pesan = text
        if pesan.startswith(rname):
            pesan = pesan.replace(rname, "", 1)
            if " & " in text:
                cmd = pesan.split(" & ")
            else:
                cmd = [pesan]
        if pesan.startswith(sname):
            pesan = pesan.replace(sname, "", 1)
            if " & " in text:
                cmd = pesan.split(" & ")
            else:
                cmd = [pesan]
        return cmd

    def access(self, good):
        u = self.master
        if good in u:
            return 0
        u = self.stats['owners']
        if good in u:
            return 1
        u = self.stats['admins']
        if good in u:
            return 2
        u = self.stats['staffs']
        if good in u:
            return 3
        u = self.stats['bots']
        if good in u:
            return 4
        u = self.stats['antijs']
        if good in u:
            return 5
        return 1000

    def notif_kick_from_group(self, op):
        kickgroup = op.param1
        kicker = op.param2
        kicked = op.param3
        if self.uid == kicked:
            if self.access(kicker) > 5:
                self.banned(kicker)
        elif self.settings["sqmode"] and kicked in self.stats["bots"]:
            if self.access(kicker) > 5:
                self.banned(kicker)
                self.client.kickoutFromGroup(kickgroup,[kicker])
                self.client.inviteIntoGroup(kickgroup,[self.stats["bots"]])
        elif self.access(kicked) < 6:
            if self.access(kicker) > 5:
                self.banned(kicker)
                self.client.kickoutFromGroup(kickgroup,[kicker])
                self.client.inviteIntoGroup(kickgroup,[kicked])
        elif kickgroup in self.settings["protect"] and self.access(kicker) > 5:
            self.client.kickoutFromGroup(kickgroup,[kicker])
            self.banned(kicker)

    def notif_invite_into_group(self, op):
        invites = op.param3.split("\x1e")
        inviter = op.param2
        group = op.param1
        if self.uid in invites:
            if self.access(inviter) < 6:
                self.client.acceptGroupInvitation(group)
        elif group in self.settings["denyinvite"]:
            if self.access(inviter) > 5:
                self.canceling(group,invites)
                self.banned(inviter)
                if self.settings["denyinvite"][group] == 2:
                    self.client.kickoutFromGroup(group,[inviter])
                    self.invites = invites
        else:
            if not set(self.stats["banned"]).isdisjoint(invites):
                nakal = set(self.stats["banned"]).intersection(invites)
                self.canceling(group,nakal)
                self.banned(inviter)
                self.invites = invites
                if self.access(inviter) > 5:
                    self.client.kickoutFromGroup(group,[inviter])
            elif inviter in self.stats["banned"]:
                self.canceling(group,invites)
                self.client.kickoutFromGroup(group,[inviter])
                self.invites = invites

    def notif_cancel_invite_group(self, op):
        group = op.param1
        canceler = op.param2
        canceles = op.param3
        if canceles != self.uid:
            if self.access(canceles) < 6:
                if self.access(canceler) > 5:
                    self.client.inviteIntoGroup(group,[canceles])
                    self.client.kickoutFromGroup(group,[canceler])
                    self.banned(canceler)
            elif group in self.settings["denyinvite"]:
                if self.access(canceler) > 5:
                    self.client.kickoutFromGroup(group,[canceler])
                    self.banned(canceler)

    def notif_update_group(self, op):
        group = op.param1
        changer = op.param2
        if op.param3 == "1":
            if group in self.settings["namelock"]:
                if self.settings["namelock"][group]["on"] == 1:
                    if self.access(changer) > 5:
                        z = self.client.getGroup(group)
                        z.name = self.settings["namelock"][op.param1]["name"]
                        self.client.updateGroup(z)
                        if group in self.settings["protect"]:
                            if self.settings["protect"][group] == 2:
                                self.client.kickoutFromGroup(group,[changer])
                                self.banned(changer)
        else:    
            if group in self.settings["linkprotect"]:
                if self.settings["linkprotect"][group] == 1:
                    if self.access(changer) > 5:
                        z = self.client.getGroup(group)
                        links = z.preventedJoinByTicket
                        if links == False:
                            z.preventedJoinByTicket = True
                            self.client.updateGroup(z)
                        if group in self.settings["protect"]:
                            if self.settings["protect"][group] == 2:
                                self.client.kickoutFromGroup(group,[changer])
                                self.banned(changer)

    def notif_accept_group_invite(self, op):
        if op.param2 in self.stats['banned']:
            self.client.kickoutFromGroup(op.param1,[op.param2])

        elif op.param2 in self.invites:
            self.client.kickoutFromGroup(op.param1,[op.param2])
            self.invites.remove(op.param2)

    def notif_leave_group(self, op):
        pass
    def accept_group_invite(self, op):
        if self.settings["autopurge"]:
            group = self.client.getGroup(op.param1)
            members = [o.mid for o in group.members]
            if not set(members).isdisjoint(self.stats["banned"]):
                band = set(members).intersection(self.stats["banned"])
                for ban in band:
                    self.client.kickoutFromGroup(op.param1,[ban])
    def receive_message(self, op):
        try:
            msg = op.message
            to = msg.to
            of = msg._from
            iz = msg.id
            text = msg.text
            if msg.contentType == 0:
                if None == msg.text:
                    return
                if text.lower().startswith(self.settings["rname"].lower() + " "):
                    rname = self.settings["rname"].lower() + " "
                else:
                    rname = self.settings["rname"].lower()
                if text.lower().startswith(self.settings["sname"].lower() + " "):
                    sname = self.settings["sname"].lower() + " "
                else:
                    sname = self.settings["sname"].lower()
                txt = msg.text.lower()
                txt = " ".join(txt.split())
                mykey = []
                if (txt.startswith(rname) or txt.startswith(sname)):
                    mykey = self.mycmd(txt, rname, sname)
                else:
                    mykey = []
                if txt == "rname" and self.access(of) < 4:
                    self.client.sendMessage(to,self.settings['rname'])
                    print(self.settings['rname'])
                if txt == "sname" and self.access(of) < 4:
                    self.client.sendMessage(to,self.settings['sname'])
                    print(self.settings['sname'])
                for a in mykey:
                    txt = a
                    if self.access(of) == 0:
                        if txt == "reboot":
                            self.client.sendMessage(to, "Restarting bot system...")
                            time.sleep(1)
                            python3 = sys.executable
                            os.execl(python3, python3, *sys.argv)
                        elif txt == "bye":
                            self.client.leaveGroup(to)
                        elif txt.startswith("namelock "):
                            jancok = txt.replace("namelock ", "")
                            if jancok == "on":
                                if to in self.settings["namelock"]:
                                    self.client.sendMessage(to,"Namelock already enabled.")
                                else:
                                    self.settings["namelock"][to] = {"on":1,"name":self.client.getGroup(to).name}
                                    self.client.sendMessage(to,"Namelock enabled.")
                            elif jancok == "off":
                                if to in self.settings["namelock"]:
                                    del self.settings["namelock"][to]
                                    self.client.sendMessage(to,"Namelock disabled.")
                                else:self.client.sendMessage(to,"Namelock already disabled.")
                        elif txt.startswith("linkprotect "):
                            jancok = txt.replace("linkprotect ", "")
                            if jancok == "on":
                                if to in self.settings["linkprotect"]:
                                    self.client.sendMessage(to,"Linkprotection already enabled.")
                                else:
                                    self.settings["linkprotect"][to] = 1
                                    group = self.client.getGroup(to)
                                    links = group.preventedJoinByTicket
                                    if links == False:
                                        group.preventedJoinByTicket = True
                                        self.client.updateGroup(group)
                                    self.client.sendMessage(to,"Linkprotection enabled.")
                            elif jancok == "off":
                                if to in self.settings["linkprotect"]:
                                    del self.settings["linkprotect"][to]
                                    self.client.sendMessage(to,"Linkprotection disabled.")
                                else:self.client.sendMessage(to,"Linkprotection already disabled.")
                        elif txt.startswith("denyinvite "):
                            jancok = txt.replace("denyinvite ", "")
                            if jancok == "max":
                                if to in self.settings["denyinvite"]:
                                    if self.settings["denyinvite"][to] == 2:
                                        self.client.sendMessage(to,"Denyinvite Max already enabled")
                                    else:
                                        self.settings["denyinvite"][to] = 2
                                        self.client.sendMessage(to,"Denyinvite Max enabled.")
                                else:
                                    self.settings["denyinvite"][to] = 2
                                    self.client.sendMessage(to,"Denyinvite Max enabled.")
                            elif jancok == "on":
                                if to in self.settings["denyinvite"]:
                                    if self.settings["denyinvite"][to] == 1:
                                        self.client.sendMessage(to,"Denyinvite already enabled")
                                    else:
                                        self.settings["denyinvite"][to] = 1
                                        self.client.sendMessage(to,"Denyinvite enabled.")
                                else:
                                    self.settings["denyinvite"][to] = 1
                                    self.client.sendMessage(to,"Denyinvite enabled.")
                            elif jancok == "off":
                                if to in self.settings["denyinvite"]:
                                    del self.settings["denyinvite"][to]
                                    self.client.sendMessage(to,"Denyinvite disabled.")
                                else:
                                    self.client.sendMessage(to,"Denyinvite already disabled.")
                        elif txt.startswith("protect "):
                            jancok = txt.replace("protect ", "")
                            if jancok == "max":
                                if to in self.settings["protect"]:
                                    if self.settings["protect"][to] == 2:
                                        self.client.sendMessage(to,"Protect Max already enabled")
                                    else:
                                        self.settings["protect"][to] = 2
                                        self.client.sendMessage(to,"Protect Max enabled.")
                                else:
                                    self.settings["protect"][to] = 2
                                    self.client.sendMessage(to,"Protect Max enabled.")
                            elif jancok == "on":
                                if to in self.settings["protect"]:
                                    if self.settings["protect"][to] == 1:
                                        self.client.sendMessage(to,"Protect already enabled")
                                    else:
                                        self.settings["protect"][to] = 1
                                        self.client.sendMessage(to,"Protect enabled.")
                                else:
                                    self.settings["protect"][to] = 1
                                    self.client.sendMessage(to,"Protect enabled.")
                            elif jancok == "off":
                                if to in self.settings["protect"]:
                                    del self.settings["protect"][to]
                                    self.client.sendMessage(to,"Protect disabled.")
                                else:
                                    self.client.sendMessage(to,"Protect already disabled.")
                        elif txt.startswith("allowban "):
                            jancok = txt.replace("allowban ", "")
                            if jancok == "on":
                                if self.settings['allowban']:
                                    self.client.sendMessage(to,"Allwoban already enabled.")
                                else:
                                    self.settings["allowban"] = True
                                    self.client.sendMessage(to,"Allwoban enabled.")
                            elif jancok == "off":
                                if self.settings['allowban']:
                                    self.settings["allowban"] = False
                                    self.client.sendMessage(to,"Allwoban disabled.")
                                else:
                                    self.client.sendMessage(to,"Allwoban already disabled.")
                        elif txt.startswith("autopurge "):
                            jancok = txt.replace("autopurge ", "")
                            if jancok == "on":
                                if self.settings['autopurge']:
                                    self.client.sendMessage(to,"Autopurge already enabled.")
                                else:
                                    self.settings["autopurge"] = True
                                    self.client.sendMessage(to,"Autopurge enabled.")
                            elif jancok == "off":
                                if self.settings['autopurge']:
                                    self.settings["autopurge"] = False
                                    self.client.sendMessage(to,"Autopurge disabled.")
                                else:
                                    self.client.sendMessage(to,"Autopurge already disabled.")
                        elif txt.startswith("squadmode "):
                            jancok = txt.replace("squadmode ", "")
                            if jancok == "on":
                                if self.settings['sqmode']:
                                    self.client.sendMessage(to,"Squadmode already enabled.")
                                else:
                                    self.settings["sqmode"] = True
                                    self.client.sendMessage(to,"Squadmode enabled.")
                            elif jancok == "off":
                                if self.settings['sqmode']:
                                    self.settings["sqmode"] = False
                                    self.client.sendMessage(to,"Squadmode disabled.")
                                else:
                                    self.client.sendMessage(to,"Squadmode already disabled.")
                        elif txt == "protection:max":
                            self.settings["protect"][to] = 2
                            self.settings["denyinvite"][to] = 2
                            self.settings["linkprotect"][to] = 1
                            group = self.client.getGroup(to)
                            self.settings["namelock"][to] = {"on":1,"name":group.name}
                            links = group.preventedJoinByTicket
                            if links == False:
                                group.preventedJoinByTicket = True
                                self.client.updateGroup(group)
                            self.client.sendMessage(to,"Max protection enabled.")
                        elif txt == "protection:none":
                            if to in self.settings["protect"]:del self.settings["protect"][to]
                            if to in self.settings["denyinvite"]:del self.settings["denyinvite"][to]
                            if to in self.settings["linkprotect"]:del self.settings["linkprotect"][to]
                            if to in self.settings["namelock"]:del self.settings["namelock"][to]
                            self.client.sendMessage(to,"All protection disabled.")
                        elif txt.startswith("uprname "):
                            string = txt.split(" ")[1]
                            self.settings['rname'] = string
                            self.client.sendMessage(to, "responsename update to {}".format(self.settings['rname']))
                        elif txt.startswith("upsname "):
                            string = txt.split(" ")[1]
                            self.settings['sname'] = string
                            self.client.sendMessage(to, "squadname update to {}".format(self.settings['sname']))
                        elif txt == "cban":
                            amount = len(self.stats["banned"])
                            self.stats["banned"] = []
                            self.client.sendMessage(to,"Unbanned %s people."%amount)
                        
        except Exception as e:
            e = traceback.format_exc()
            if "EOFError" in e:
                pass
            elif "ShouldSyncException" in e or "LOG_OUT" in e:
                python3 = sys.executable
                os.execl(python3, python3, *sys.argv)
            else:
                traceback.print_exc()
