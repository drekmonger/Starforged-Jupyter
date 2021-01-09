#!/usr/bin/env python
# coding: utf-8

# In[87]:


import json, random, re
from collections import defaultdict
from itertools import count
from copy import deepcopy, copy


from IPython.display import display, HTML, Markdown


# In[88]:


if not "PATH" in globals():
    PATH=""

with open(PATH + "starforged.css", "r") as file:
    display(HTML(file.read()))


# ## Settings

# In[89]:


ruleoption_match_on_even_only = True


# ## Consts

# In[90]:


result_types = ["Miss", "Weak Hit", "Strong Hit"]

#pc traits
edge = "edge"
heart = "heart"
iron = "iron"
shadow = "shadow"
wits = "wits"

momentum = "momentum"
health = "health"
spirit = "spirit"
supply = "supply"

#ranks
magnitude_types = [("Troublesome", 3), 
                   ("Dangerous", 2), 
                   ("Formidable", 1),
                   ("Extreme", .5), 
                   ("Epic", .25)]
troublesome = 0
dangerous = 1
formidable = 2
extreme = 3
epic = 4
                   
#vow types
vow = "Vow"
battle = "Battle"
expedition = "Expedition"
connection = "Connection"
legacy = "Legacy"

track_types = ['Vow', 'Legacy', 'Connection', 'Expedition', 'Combat']

regions = ["Terminus", "Outlands", "Expanse"]
                   
#dice
def d6():
    return random.randint(1,6)

def d10():
    return random.randint(1,10)

def d100():
    return random.randint(1,100)

#oracle consts
certain = .9
likely = .75
fifty_fifty = .5
unlikely = .25
small_chance = .1

def chance (percentage):
    if random.random() < percentage:
        return True
    else:
        return False


# ## Utility Functions

# In[91]:


str_join = "&ensp;⁃&ensp;"
str_bullet = "&emsp;◦&emsp;"
str_head = "#### "

def str_ss (string):
    return f"<span style='font-family: \"Cuprum\", sans-serif; font-size:1.5em;'>{string}</span>"

def str_emphasis (string):
    return f"<span style='font-family: \"Cuprum\", sans-serif; font-size:1.25em; font-style:bold'>{string}</span>"

def str_textbox (string, color="#eef5f5"):
    return f"<div style='background-color: {color}; color:black; width: 460px; padding: 10px;'>{string}</div>"

def str_callout(string, bcolor="black", fcolor="white"):
    return f"<div style='background-color:{bcolor}; color:{fcolor}; height:30px; width: 350px; text-align: center; padding: 2px;'>{string}</div>"

def str_italic(string):

    return f"<span style='font-style:italic'>{string}</span>"


def html_list_item(string, depth):
    return f"<span style = 'font-family: \"Cuprum\", sans-serif; font-size:1.2em;'> {'— '*depth} {string} </span>"


def _listing (function, length = 3):
    text = []
    for _ in range(length):
        text.append(f"{function()}")
    return str_bullet.join(text)

def print_list (function, length = 5):
    printmd(_listing(function, length))


# In[92]:


def _convert_label_to_attr_str (label_str):
    return label_str.lower().replace(" ", "_")

def printmd (obj):
    
    if type(obj) == str:
        display(Markdown(obj))
    else:
        display(obj)
            


# ## Fields

# In[93]:


class Field():
    
    def __init__(self, factory_cls, *args, **kwargs):
        if "label" in kwargs.keys():
            self.label = kwargs["label"]
        else:
            self.label = None
            
        self.factory_cls = factory_cls
            
        self.dict = defaultdict(lambda: factory_cls(self.label, *args, **kwargs))
        
    def __set_name__(self, owner, name):
        if self.label == None:
            self.label = name
        if hasattr(owner, "_register_field"):
            owner._register_field(self.factory_cls, name)
        
    
    def __get__(self, instance, instance_cls=None):
        return self.dict[instance]
    
    def __set__(self, instance, value):
        self.dict[instance]._owner = instance
        self.dict[instance].value = value    


# In[ ]:





# ### Entry Classes
# 
# Children of this class should always implement: `reset()`, `clear(value)`, `mark(value)`, `_validation_hoook(value)`, and `_coercion_hook(value)`.

# In[94]:


class Entry():
    def __init__(self, label, value=""):
        self.label = label
        self._value = value
        self._display_on_update = False
    
    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, value):
        
        if value==self:
            return
        
        old_value = self._value
        
        value = self._other_field_check(value)
        value = self._validation_hook(value)
        self._value = self._coercion_hook(value)
        
        if hasattr(self, "_owner"):
            if hasattr(self._owner, "_handle_field_update"):
                self._owner._handle_field_update(self)
        
        if self._display_on_update:
            display(self)
   
    def _validation_hook(self, value):
        return value

    def _coercion_hook(self, value):
        return str(value)
    
    def reset(self):
        self.value = ""
    
    def clear(self, value = ""):
        self.value = ""
        
    def set(self, value):
        self.value = value
    
    def _handle_stat_update(self, _, old_value, value):
        pass
    
    def __str__(self):
        return f"{self.label}: {self._value}"
    
    def _other_field_check (self, other):
        if issubclass(type(other), Field):
            return other.value
        return other
    
    def __eq__(self, other):
        return self._value== self._other_field_check(other)
    
    def __ne__(self, other):
        return self._value!= self._other_field_check(other)
    
    @property
    def _html(self):
        return f"<div class='field'><div class='fieldlabel'>{self.label.title()}<div class='label ypesuff'>{self.value}</div></div></div>"
    
    def _ipython_display_(self):
        display(HTML(self._html))
        
    #TODO display, fix _handle_stat, debug
    


# ### Stat class

# In[95]:


class Stat(Entry):
    def __init__(self, label, default=2, min_value=0, max_value=5):
        
        super().__init__(label = label)
        
        self._default  = default
        self._value = default
        self.min_value = min_value
        self.max_value = max_value
        
        self._display_on_update = False
        
    
    def _validation_hook(self, value):
        
        if not (type(value)==int or type(value)==float or type(value)==bool):
            raise TypeError("Must be numeric.")

        value = max(value, self._min_value)
        value = min(value, self._max_value)
        return value
    
    def _coercion_hook(self, value):
        return int(value)
    
    @property
    def max_value(self):
        return self._max_value
    
    @max_value.setter
    def max_value(self, value):
        self._max_value = value
        if self._max_value < self._value:
            self._value = self._max_value
    
    @property
    def min_value(self):
        return self._min_value
    
    @min_value.setter
    def min_value(self, value):
        self._min_value = value
        if self._min_value > self._value:
            self._value = self._min_value
    
   
    
    def reset (self):
        self.value = self._default
        
    def clear (self, value = 0):
        self.value = 0
    
    def mark (self, value = 2):
        self.value = value

    def __int__(self):
        return int(self.value)
    
    def __float__(self):
        return float(self.value)
    
    def __nonzero__(self):
        if self.value == 0:
            return False
        return True
    
    def __add__(self, other):
        return self.value + other
        
    def __iadd__(self, other):
        self.value += other
        return self
        
    def __sub__(self, other):
        return self.value - other
    
    def __isub__(self, other):
        self.value -= other
        return self
    
    def _other_field_check (self, other):
        if issubclass(type(other), Stat):
            return other.value
        return other
    
    def __lt__(self, other):
        return self.value < self._other_field_check(other)
    
    def __le__(self, other):
        return self.value <= self._other_field_check(other)
        
    def __ge__(self, other):
        return self._value>= self._other_field_check(other)
    

    @property
    def _html(self):
        return f"<div class='stat'><div class='bignumber'>{self.value}</div>{self.label}</div>"
    
    def _ipython_display_(self):
        display(HTML(self._html))
        
class PCStat(Stat):
    pass


# ### Impact class

# In[96]:


class Impact(Stat):
    def __init__(self, label):
        super().__init__(label=label, default = False, min_value = False, max_value = True)
        self._display_on_update = False
        
    def __str__(self):
        if self==True:
            return f"{self.label}: True"
        else:
            return f"{self.label}: False"
    
    def _coercion_hook(self, value):
        return bool(value)
    
    def mark(self, value = 1):
        self.value = True
    
    def clear(self, value = 0):
        self.value = False
        
    def set(self):
        self.value = True
        
    def unset(self):
        self.value = False    
        
    @property
    def _html(self):
        if self.value==False:
            return f"<div class='impact'>○ {self.label}</div>"
        elif self.value == True:
            return f"<div class='impact set'>✘ {self.label}</div>"
        else:
            return f"<div>{self.label} {self.value}</div>"
        
    def _ipython_display_(self):
        display(HTML(self._html))


# ### StatMeter class

# In[97]:


class StatMeter(Stat):
    def __init__(self, label, default=5, min_value=0, max_value=5):
        super().__init__(label=label, default=default, min_value=min_value, max_value=max_value)
        self._display_default = False
        self._display_on_update = True
    
    @property
    def _html(self):
        html = "<div class='meter-container'>"
        html += f"<div class= 'label'>{self.label.title()}"
        
        if self._display_default:
            html += f"<span class='smalltext'> Reset: {self._default}</span>"
        
        html += "</div>"
        html += "<div class='flex-meter'>"
        for i in range(self._min_value, self._max_value+1):
            if i == self.value:
                html += f"<div class='meter-number set'>{i}</div>"
            else:
                html += f"<div class='meter-number'>{i}</div>"
        html += "</div></div>"
        return html
    
    def mark(self, amount=1):
        self.value += amount
        
    def clear(self, amount=1):
        self.value -= amount
    
    def _ipython_display_(self):
        display(HTML(self._html))

class Momentum(StatMeter):
    def __init__(self, label = "Momentum"):
        super().__init__(label=label, default=2, min_value=-6, max_value=10)
        self._display_default = True


# ### ProgressMeter class

# In[98]:


class ProgressMeter(Stat):
    def __init__ (self, label="Progress", rank=1, text="", kind="Progress"):
        super().__init__( label=label, default=0, min_value=0, max_value=10)
        self.kind = kind
        self.text = text
        self.rank = rank
        self.archived = False
        self.threat = ""
        self.threat_value = 0
        self._display_on_update = True
        
    def _coercion_hook(self, value):
        return float(value)
        
    def mark(self, amount=None):
        if amount == None:
            self.value += magnitude_types[self.rank][1]
        else:
            self.value += amount
        
    def mark_twice(self):
        self.value += magnitude_types[self.rank][1] * 2
    
    def clear(self, amount = None):
        if amount == None:
            self.value -= magnitude_types[self.rank][1]
        else:
            self.value -= amount
            
    def clear_all(self):
        self.value = 0
        
    def clear_all_but_one(self):
        self.value = 1
        
    def archive(self):
        self.archived = True
        if hasattr(self, "_owner"):
            self._owner._handle_field_update(self)

    @property
    def _html(self):
        
        html = f"<div class='label'>{self.label}{str_join}<span class='normalize-font'>{magnitude_types[self.rank][0]} {str(self.kind)}</div>"
        
        html += self._html_pre_hook
        
        html += self._html_threat
        
        html += "<div class ='flex-stat-container'>"
        
        for i in range(10):
            if self.value >= i+1:
                html += "<div class='progress full'></div>"
            else:
                if (i - self.value) >= 0:
                    html += "<div class='progress'></div>"
                else:
                    decimal = i - self.value
                    if decimal==-.25:
                        html += "<div class='progress onetick'></div>"
                    if decimal==-.50:
                        html += "<div class='progress twoticks'></div>"
                    if decimal==-.75:
                        html += "<div class='progress threeticks'></div>"
            
        html += "</div>"
        
        html += self._html_post_hook
        
        html += f"<div class='normalize-font'>{self.text}</div>"
        
        if not self.threat == "":
            html += f"<div class='normalize-font'>Threat: {self.threat}</div>"
        
        return html
    
    @property
    def _html_threat(self):
        if self.threat == "" and self.threat_value == 0:
            return ""
        
        html = "<div class = 'flex-stat-container'>"
        for i in range(10):
            if self.threat_value >= (i+1):
                html += "<div class='menace set'></div>"
            else:
                html += "<div class='menace'></div>"
        
        html += "</div>"
        
        return html
        
    @property
    def _html_pre_hook(self):
        return ""
    
    @property
    def _html_post_hook(self):
        return ""


# In[99]:


class _Dummy_Track(ProgressMeter):
    
    def __init__(self):
        super().__init__( label="placeholder", rank = 0 )
        
    def mark(self, amount=None):
        pass
    
    def mark_twice(self):
        pass
    
    def clear(self, amount = None):
        pass
    
    def clear_all(self):
        pass
        
    def clear_all_but_one(self):
        pass
    
    def archive(self):
        pass
        
    @property
    def _html(self):
        return ""
    
    def _ipython_display_(self):
        pass

_dummy_track = _Dummy_Track()


# ### Stat Tester

# In[100]:


class Tester ():
    
    test = []
    name = Field(Entry)
    wits = Field(Stat)
    momentum = Field(Momentum)
    foo = Field(Impact)
    bar = Field(StatMeter)
    fizz = Field(ProgressMeter, rank=4)
    
    def __init__(self):
        pass
    
    def _handle_field_update(self, obj):
        print("update called on: " + str(obj))
        
    def _register_field(cls, label):
        pass
        #print(str(cls) + ":" + label)


# ## Category Bin

# In[101]:



# Essentially abstract. Needs _data and _categories to be filled in _init__, before calling super()
# Also self._desc set, for example to "Moves"
# methods _do and _print_item
# likely requires subclassing _item_template to do more interesting thigns

class _CategoryBin():
    
    def __init__(self):
        for cat, move_list in self._categories.items():
            cat_obj = self._item_category(self, cat, move_list)
            setattr(self, cat.lower(), cat_obj)
    
    def __call__(self, cat=None):
        self.list(cat)
    
    def _ipython_display_(self):
        self()
    
    def list (self, cat=None):
        def print_cat(cat): 
            printmd(str_emphasis(cat + " " + self._desc))
            output = []
            for key, item in self._data.items():
                if item["Category"]==cat:
                    output.append(key)
                
            printmd(str_bullet.join(output))
            
        #print all the items if no category passed in
        if cat == None or cat == "":
            for category in self._categories:
                print_cat(category)
            
        #if the category doesn't exist, print out the categories
        elif not cat in self._categories:
            printmd(str_emphasis(self._desc + " Categories"))
            printmd(f"**{str_bullet.join(self._categories)}**")
        else:
            print_cat(cat)
    
    def _print_item(self, item = None):
        print(item)
    
    def _do(self, item):
        print('Do: ' + item)
            
    class _item_category():
       
        def __init__(self, parent, name, items_list):
            self._parent = parent
            self._name = name
            for item in items_list:
                attr = _convert_label_to_attr_str(item)
                reference = getattr(parent, attr)
                setattr(self, attr, reference)
                
        def __call__(self):
             self._parent.list(self._name)
        
        def _ipython_display_(self):
            self()
            
class _item_template():
    def __init__(self, parent, name):
        self.name = name
        self.parent = parent
            
    def __call__(self):
        self.parent._do(self.name)
            
    def _ipython_display_(self):
        self.parent._print_item(self.name)
        


# In[ ]:





# ## Binder

# In[102]:


class Binder ():
    def __init__(self, name="Binder"):
        self._dict = {}
        self._child_binders = defaultdict(Binder)
        self._name = name
        self._index = count(0)
    
    def __len__(self):
        return len(self._dict)
    
    def __contains__(self, item):
        if item in self._dict:
            return True
        return False
    
    def exists(self, key):
        if key in self._dict:
            return True
        else:
            printmd("*No such entry exists.*")
            return False
    
    def __getitem__(self, key):
        
        if not (isinstance(key, str) or isinstance(key, int)):
            raise TypeError()
        
        if self.exists(key):
            return self._dict[key]
        else:
            printmd("*No item found.*")
            return None
        
    def __setitem__(self, key, value):
        self.add(value, key)
    
    def __delitem__(self, key):
        if not isinstance(key, str):
            raise TypeError()
        
        if key in self._tracks:
            del self._dict[key]
        else:
            raise IndexError()
    
    def __iter__(self):
        return iter(self._dict)
    
    def __getattr__(self, item):
        if item[0]=="_":
            raise AttributeError()
        self._child_binders[item]._name = item
        return self._child_binders[item]
    
    def __dir__(self):
        directory = list(self._child_binders.keys())
        directory.extend(['add', 'append', 'remove', "remove_child_binder"])
        return directory
    
    def add(self, obj, key=None, silent=False):
        
        if key == None:
            key = next(self._index)
        
        if not (isinstance(key, str) or isinstance(key, int)):
            raise TypeError()
            
        self._dict[key] = deepcopy(obj)
        
        if not silent:
            printmd(f"*Added `{key}` to {self._name}.*")
            
    def append(self, obj):
        self.add(obj, silent=True)
    
    def remove(self, label):
        if not label in self._dict:
            printmd("*No such label exists in the binder.*")
        
        del self._dict[label]
        
    def remove_child_binder(self, label):
        
        if not type(label) == str:
            printmd("Use a string, ie, 'child'.")
            return
        
        if label in self._child_binders:
            del self._child_binders[label]
        else:
            printmd("*No such child binder found.*")
        
    def _ipython_display_(self):
        
        if len(self._dict)==0 and len(self._child_binders)==0:
            printmd(f"*{self._name.title()} is empty.*")
            return
        
        printmd (str_ss(self._name.title()))
        
        if len(self._child_binders)>0:
            child_str = " ".join(self._child_binders.keys())
            printmd(f"Child binders: {child_str}")
        
        
        for key, item in sorted(self._dict.items()):
            printmd("______")
            printmd(str_emphasis(key))
            printmd(item)
        
        
            
    def _ipython_key_completions_(self):
        return self._dict.keys()
    
binder = Binder()  
    


# In[ ]:





# In[ ]:





# ## Oracle

# In[103]:


class _Oracle_Response():
    def __init__(self, obj):
        self.obj = obj
        
    def _ipython_display_(self):
        printmd(self.obj)



class Oracles():
    
    def __init__(self):
        self._results = []
        self._results.append("Oracle Results")
        
    def __len__(self):
        return len(self._dict)
    
    def __getitem__(self, key):
        
        if not isinstance(key, int):
            raise TypeError()
        
        if 1 <= key < len(self._results):
            return self._results[key]
        else:
            printmd(f"Invalid key. There are {len(self._results)-1} entries.")
            return 'Invalid oracle.'
                    
    def __iter__(self):
        return iter(self._results)
    
    ##Oracle stuff
    
   
    
    def _select(self, oracle, category):
        data_attr = "_data_" + oracle
        
        if hasattr(self, data_attr):
            data = getattr (self, data_attr)
        else:
            with open(PATH + f"Data/starforged_oracles_{oracle}.json", "r") as file:
                data = json.load(file)
            setattr (self, data_attr, data)
        
        category_data = data["Oracles"][category]
        region = None
        
        if "Outlands" in data["Oracles"][category][0].keys():
            region = random.choose(regions)
            category_data = data["Oracles"][category][region]
        
        selection = self._select_items(category_data)
            
        return (region, selection)
    
    def _select_items(self, category_data):
        selection = [(self._select_weighted(category_data))]
        selection[0]["Depth"] = 0
        
        #should be done recursively, but ran into errors, and it's too much of an edge case to worry about
        if selection[0]["Description"] == "[Roll twice]":
            for _ in range(2):
                selection.append(self._select_weighted(category_data))
                selection[-1]["Depth"] = 1
        
        if selection[0]["Description"] == "[Roll thrice]":
            for _ in range(3):
                selection.append(self._select_weighted(category_data))
                selection[-1]["Depth"] = 1
        
        return selection
                
    def _select_weighted (self, entries):
        choice = d100()
        
        #choice = random.randint(90, 100) #uncomment to check higher range weirdness
         
        for entry in entries:
            if choice<= entry["Chance"]:
                return entry
        
    
    def _select_simple (self, oracle, category):
        return self._select(oracle, category)[1][0]["Description"]
    
    def _print(self, obj, id):
        
        id = f"<div class='round-number'>oracle[{id}]</div>"
        
        printmd(obj)
        printmd(id)
    
    def _respond(self, obj):
        current_id = len(self._results)
        
        obj = _Oracle_Response(obj)
        
        self._results.append(obj)
        
        self._print(obj, current_id)
        
    
    def _select_and_respond (self, oracle, category):
        
        selection = self._select(oracle, category)[1]
        response = []
                
        for item in selection:
            cat_string = str_italic(category) + str_bullet if item['Depth']==0 else ""
            response.append(cat_string + html_list_item(item['Description'], item['Depth']).strip())

        response = "<br>".join(response)
        
        self._respond(response)
        
    #user-facing oracles
    def ask (self, question="Yes or no?", percent_chance=.5, response1="Yes", response2="No"):
        
        if chance(percent_chance):
             response = str_emphasis(question + str_join + response1)
        else:
            response = str_ss(question + str_join + response2)
        
        self._respond(response)
    
    def inspire(self):
        oracle = "interpretive"
        action = self._select_simple(oracle, "Action")
        theme = self._select_simple(oracle, "Theme")
        descriptor = self._select_simple(oracle, "Descriptor")
        focus = self._select_simple(oracle, "Focus")
        
        response = str_emphasis(f"{action} {theme}{str_bullet}{descriptor} {focus}")
        
        self._respond (response)
        
    
    #campaign start oracles
    def launch_backstory(self):
        self._select_and_respond("campaign_start", "Backstory Prompts")
    
    def launch_starship_history(self):
        self._select_and_respond("campaign_start", "Starship History")
    
    def launch_starship_quirks(self):
        self._select_and_respond("campaign_start", "Starship Quirks")
    
    def launch_sector_trouble(self):
        self._select_and_respond("campaign_start", "Sector Trouble")
    
    def launch_inciting_incident(self):
        self._select_and_respond("campaign_start", "Inciting Incident")
    
    def launch_campaign(self):
        self.launch_backstory()
        self.launch_starship_quirks()
        self.launch_starship_quirks()
        self.launch_sector_trouble()
        self.launch_inciting_incident()

    
    
    #move oracles
    def pay_the_price(self):
        self._select_and_respond("moves", "Pay the Price")
        
    def make_a_discovery(self):
        self._select_and_respond("moves", "Make a Discovery")
    
    def confront_chaos(self):
        self._select_and_respond("moves", "Confront Chaos")
    
    def take_decisive_action(self):
        self._select_and_respond("moves", "Take Decisive Action")
    
    def endure_harm(self):
        self._select_and_respond("moves", "Endure Harm")
        
    def endure_stress(self):
        self._select_and_respond("moves", "Endure Stress")
    
    def withstand_damage(self):
        self._select_and_respond("moves", "Withstand Damage")
        
    
    def _ipython_display_(self):
        printmd ("**Oracle**")
        
        for i, item in enumerate(self, start=0):
            if i == 0:
                continue
            printmd('___')
            self._print(item, i)
        
oracle = Oracles()


# In[ ]:





# ## Setting Truths

# In[104]:


def _Truths ():
    with open(PATH + f"Data/starforged_setting_truths.json", "r") as file:
        data = json.load(file)
    catagory = data["Setting Truths"]
    
    for entry in catagory:
        
        choice = random.choice(catagory[entry]["Truths"])
        
        if "Suboracle" in choice.keys():
            subchoice = str_italic(random.choice(choice["Suboracle"]))
        else:
            subchoice = ""
        yield (entry, choice, subchoice)
    raise StopIteration()
    
_i_truths = _Truths()


def truth ():
    global _accumulated_truth
    
    try: 
        current = next(_i_truths)
        html = "<div>"
        html += f"<div class='category paintitblack'>{current[0]}</div>"
        html += str_textbox(str_emphasis(current[1]['Summary']))
        html += str_textbox(f"{current[1]['Description']}&ensp;{current[2]}")
        html += str_textbox(str_italic("Quest") + str_join + current[1]['Quest'], "beige")
        html += "</div>"
        
        oracle._respond(html)
        
        binder.truths.add(html, silent=True)
        
    except:
        printmd("___")
        printmd(str_italic("That's the end of the truths. Try `oracle.lauchcampaign` for the next step or `truth_reset()` to try again."))
        printmd("___")
        
def truth_reset():
    global _i_truths
    binder.remove_child_binder("truths")
    _i_truths = _Truths()


# ## Progress Track Sheet

# In[105]:


class Track_Sheet():
    def __init__(self):
        self._tracks = {}
        self._dh = None
        
        
    def __getstate__(self):
        tracker_state = {}
        
        for attr, obj in self._tracks.items():
            tracker_state[attr] = obj.__dict__
        return tracker_state 
        
    def __setstate__(self, state):
        
        self.__init__()
        
        for attr, obj in state.items():
            self._tracks[attr] = ProgressMeter()
            self._tracks[attr].__dict__ = obj
            self._tracks[attr]._owner = self
        
    
    def __len__(self):
        return len(self._tracks)
    
    def __contains__(self, item):
        if item in self._tracks:
            return True
        return False
    
    def exists(self, key):
        if key in self._tracks:
            return True
        else:
            printmd("*No such progress track exists.*")
            return False
    
    def __getitem__(self, key):
        
        if not isinstance(key, str):
            raise TypeError()
        
        if self.exists(key):
            return self._tracks[key]
        else:
            return _dummy_track
        
        
    def __setitem__(self, key, value):
        
        
        if not isinstance(key, str):
            raise TypeError()
        
        if isinstance(value, ProgressMeter):
            self._tracks[key]=value
        else:
            if isinstance(value, (int, float)) and key in self._tracks:
                self._tracks[key].value = value
            else:
                printmd ("*The tracker can only contain Progress Trackers.*")
            
    def __delitem__(self, key):
        if not isinstance(key, str):
            raise TypeError()
        
        if key in self._tracks:
            del self._tracks[key]
        else:
            raise IndexError()
    
    def __iter__(self):
        return iter(self._tracks)
    
    #track functions
    
    def add (self, label=None, kind="Vow", rank=1, text="", display_track_now=True):
        
        if label==None:
            printmd('Syntax: `add_track("*short label*", vow|battle|connection|etc, troublesome|dangerous|etc, "*optional longer description*")`')
            printmd("Use `tracker['*short label*']` to reference the track.")
            return
        
        if label in self._tracks:
            printmd("*Progress track with that label already exists.*")
        else:
            self._tracks[label] = ProgressMeter(label=label, rank=rank, text=text, kind=kind)
            self._tracks[label]._owner = self
            if display_track_now:
                display(self[label])
                
    def _add_error_msg(self, function_str):
        printmd(f'Syntax: `add_{function_str}("*short label*", troublesome|dangerous|etc, "*optional longer description*")`')
        
    def add_vow (self, label=None, rank=1, text=""):
        if label==None:
            self._add_error_msg("vow")
            return
        self.add(label=label, kind="Vow", rank=rank, text=text)
    
    def add_connection(self, label=None, rank=1, text=""):
        if label==None:
            self._add_error_msg("connection")
            return
        self.add(label=label, kind="Connection", rank=rank, text=text)
    
    def add_expedition(self, label=None, rank=1, text=""):
        if label==None:
            self._add_error_msg("expedition")
            return
        self.add(label=label, kind="Expedition", rank=rank, text=text)
    
    def add_objective (self, label=None, rank=1, text=""):
        if label==None:
            self._add_error_msg("objective")
            return
        self.add(label=label, kind="Objective", rank=rank, text=text)
    
    def add_combat (self, label=None, rank=1, text=""):
        self.add(label=label, rank=rank, text=text)
    
    def _add_legacy (self, label):
        self.add(label=label, kind="Legacy", rank=epic, text="", display_track_now=False)
    
    
    def mark_progress(self, key, amount=None):
        if self.exists(key):
            self[key].mark(amount)
    
    def mark_progress_twice(self, key):
        if self.exists(key):
            self[key].mark_twice()
    
    def clear(self, key, amount=None):
        if self.exists(key):
            self[key].clear(amount)
    
    def clear_all_progress(self, key):
        if self.exists(key):
            self[key].clear_all()
    
    def clear_all_progress_but_one(self, key):
        if self.exists(key):
            self[key].clear_all_but_one()
    
    def threat_describe(self, key, text):
        if self.exists(key):
            self[key].threat = text 
    
    def archive (self, key):
        if self.exists(key):
            self[key].archive()
    
    def remove (self, key):
        if self.exists(key):
            del (self[key])
            
    def show_archived(self):
        display(HTML(self._html(archived=True)))    
    
    #display
    
    def _handle_field_update(self, obj):
        self._update_display()
    
    def _html(self, archived=False):
        # find out which categories are present
        
        def archive_choice(track_data):
            return (track_data.archived == False and archived==False) or (track_data.archived==True and archived==True)
        
        html = "<div class='catlist sheet'>"
        categories = []
        
        for track, track_data in self._tracks.items():
            if archive_choice(track_data):
                categories.append(track_data.kind)
        
        categories = set(categories)
        
        for category in categories:
            html += f"<div class = 'category'>{category}s</div>"
            for track, track_data in self._tracks.items():
                if track_data.kind == category and archive_choice(track_data):
                    html += track_data._html
        
        html += "</div>"
        return html
        
    def _ipython_display_(self):
        self._dh = display(HTML(self._html()), display_id = True)
        
    def _update_display(self, change = ""):
        if not self._dh==None:
            self._dh.update(HTML(self._html()))
        
    def _ipython_key_completions_(self):
        return self._tracks.keys()
    
tracker = Track_Sheet()


# In[ ]:





# ## Assets
# 

# In[106]:


class Asset():
    name = ""
    kind = ""
    
    aspects = []
    input_fields = []
    
    
class Asset_Container:
    
    def __init__(self):
        with open(PATH + "Data/starforged_assets.json", "r") as file:
            file.data = json.load(file)
        

test_assets = Asset_Container()


# In[ ]:





# ## Player Character

# In[107]:


class Player_Character():
    
    #basic stats
    name = Field(Entry)
    
    edge = Field(PCStat)
    heart= Field(PCStat)
    iron = Field(PCStat)
    shadow = Field(PCStat)
    wits = Field(PCStat)
    
    health = Field(StatMeter)
    spirit = Field(StatMeter)
    supply = Field(StatMeter)
        
    momentum = Field(Momentum)
        
    #conditions
    wounded = Field(Impact)
    shaken = Field(Impact)
    unprepared = Field(Impact)
    encumbered = Field(Impact)
    
    #lasting
    
    scarred = Field(Impact)
    traumatized = Field(Impact)
    
    #burdens
    doomed = Field(Impact)
    tormented = Field(Impact)
    indebted = Field(Impact)
    
    #current vehicle
    battered = Field(Impact)
    cursed = Field(Impact)
    
    _impacts = []
    _PCstats = []

    @classmethod
    def _register_field (self_cls, incoming_cls, name):
      
        if incoming_cls == PCStat:
            self_cls._PCstats.append(name)
        if incoming_cls == Impact:
            self_cls._impacts.append(name)
    
    def __init__(self, name = ""):    
        self._dh = None
        
        #vows, assets, and legacies
        #self.assets = Asset_Container
        
        self.vows = Track_Sheet()
        
        self.legacies = Track_Sheet()
        self.legacies._add_legacy("Quests")
        self.legacies._add_legacy("Bonds")
        self.legacies._add_legacy("Discoveries")
        
        self.binder = Binder()
        
    
    def __getstate__(self):
        
        vows_state = self.vows.__getstate__()
        legacies_state = self.legacies.__getstate__()
        binder_state = self.binder
        
        field_state = dict()
     
        for attr, obj in type(self).__dict__.items():
            if type(obj) == Field:
                field_state[attr] = getattr(self, attr).__dict__
        return (vows_state, legacies_state, binder_state, field_state)
    
    def __setstate__(self, state):
        self.vows = Track_Sheet()
        self.vows.__setstate__(state[0])
        self.legacies = Track_Sheet()
        self.legacies.__setstate__(state[1])
        self.binder = state[2]
        
        
        for key, dic in state[3].items():
            field = getattr(self, key)
            for attr, value in dic.items():
                if attr == "_owner":
                    setattr(field, attr, self)
                else:
                    setattr(field, attr, value)
                   
    
    @property
    def assets(self):
        return self.binder.assets
    
    
    def count_impacts(self):
        count = 0
        for impact in type(self)._impacts:
            if getattr(self, impact).value:
                count += 1
        return count

    def _handle_field_update(self, obj):
        
        if isinstance(obj, Impact):
            self.momentum._default = max(2-self.count_impacts(), 0)
            self.momentum.max_value = 10 - self.count_impacts()
        else:

            if obj.label == "supply":
                if self.supply == 0 and self.unprepared == False:
                    self.unprepared = True
            
            if isinstance(obj, PCStat):
                printmd (f"*{obj.label.title()} changed to {obj.value}.*")
        
        self._update_display(self)
    

    @property
    def _html(self):
        html = "<div class = 'sheet'>"
        html += self.name._html
        
        html += "<div class='flex-stat-container'>"
        for stat in type(self)._PCstats:
            html += getattr(self, stat)._html
        html += "</div>"
        html += "<div>"
        
        html += self.health._html
        html += self.spirit._html
        html += self.supply._html
        html += "</div>"
        
        html += "<div></div>"
        html += self.momentum._html
        
        html += "<div class='flex-stat-container'>"
        html += self._html_impact_category("Conditions", [self.wounded, self.shaken, self.unprepared, self.encumbered])
        html += self._html_impact_category("Lasting Effects", [self.scarred, self.traumatized])
        html += self._html_impact_category("Burdens", [self.doomed, self.tormented, self.indebted])
        html += self._html_impact_category("Current Vehicle", [self.battered, self.cursed])
        html += "</div>"
        html += "</div>"
        
        return html
    

    def _html_impact_category(self, category, impacts):
        html = ""
        html += "<div class='spacer-impact'>"
        html += f"<span class='label'>{category}</span>"
        html += "<div class = 'flex-impact-container'>"
        
        for impact in impacts:
            html += impact._html
        
        html += "</div></div>"
        
        return html
        
    def _ipython_display_(self):
        self._dh = display(HTML(self._html), display_id = True)
        
    def _update_display(self, change = ""):
        if not self._dh==None:
            self._dh.update(HTML(self._html))
    
    
pc = Player_Character()


# In[ ]:





# ## Dice

# In[ ]:





# In[108]:


class _roll():
    
    def __init__(self, move = None, progress_target=("", -1), mod=0, trait = (0,"", None)):
        self.move = move
        
        self.progress_label, self.progress_target = progress_target
    
        self.mod = mod
        
            
        self.trait_label, self.trait_value, self.trait_owner = trait
        
        self.d6 = d6()
        self.c1 = d10()
        self.c2 = d10()
        self._memo = None
        
        self._momentum_override = None

    @property
    def score(self):
        
        if self.progress_target>0:
            return self.progress_target
        
        if not self._momentum_override == None:
            return self._momentum_override
        
        d6 = self.d6
        
        if not self.trait_owner == None:
            if d6 == (self.trait_owner.momentum.value*-1):
                d6 = 0
                
        return d6 + self.mod + self.trait_value

    @property
    def success(self):
        success = 0
        if self.score>self.c1:
            success +=1
        if self.score>self.c2:
            success +=1 
        
        return success
    
    @property
    def memo(self):
        
        if not self._memo==None:
            return self._memo

        if self.progress_target>0:
            if self.progress_label == "":
                return (f"Rolled against a progress of {self.progress_target}.")
            else:
                return (f"Rolled for progress on {self.progress_label}({self.progress_target}).")
        
        if self.trait_label=="":
            return (f"Rolled +{self.mod + self.trait_value}.")
    
        if self.mod==0:
            return (f"Rolled +{self.trait_label} ({self.trait_value}).")
        else:
            return (f"Rolled +{self.trait_label} ({self.trait_value})+{self.mod}.")
    
    @memo.setter
    def memo(self, value):
        self._memo = value
        
        
    def _caveats(self):
        text = []
        success = self.success
        
        if not (ruleoption_match_on_even_only and self.c1 % 2 == 1):
            if self.c1 == self.c2 and not self.c1 == 0:
                if success == 0:
                    text.append(str_emphasis("Complication! "))
                else:
                    text.append (str_emphasis("Opportunity! "))
        
        if not self.trait_owner == None:
            
            momentum = self.trait_owner.momentum.value
            
            if self.d6==momentum * -1 and self.progress_target>0:
                text.append (f"Action die of {self.d6} was canceled by negative momentum. ")
        
            if success==0:
                if momentum > self.c1 and momentum > self.c2:
                    text.append ("Burn momentum for a strong hit.")
                elif momentum > self.c1 or momentum > self.c2:
                    text.append("Burn momentum for a weak hit.")
        
            if success==1:
                if (self.c1 >= self.score and momentum > self.c1) or (self.c2 >= self.score and momentum > self.c2):
                    text.append("Burn momentum for a strong hit.")
        
        return ("<br>".join(text))
    
   
    
    def _repr_markdown_(self):
        if self.progress_target>0:
            results_html = str_callout(f"Target {str_ss(self.progress_target)}{str_bullet}Challenge {str_ss(f'{self.c1} ‖ {self.c2}')}", '#eef5f5', 'black')
        else:
            results_html =  str_callout(f"Action Die {str_ss(self.d6)}{str_bullet}Score {str_ss(self.score)}{str_bullet}Challenge {str_ss(f'{self.c1} ‖ {self.c2}')}", '#eef5f5', 'black')
        
        if self.move==None:
            move_html = ""
            effect_md = ""
        else:
            move_html = str_emphasis(self.move["Name"]) + " — "
            if self.success == 2:
                effect_md = self.move["Strong"]
            if self.success == 1:
                effect_md = self.move["Weak"]
            if self.success == 0:
                effect_md = self.move["Miss"]
                
            if effect_md == None:
                effect_md = self.move["Text"]
            
            effect_md = "<br>" + str_textbox(effect_md)
            
        
        return (move_html + str_italic(self.memo) + str_callout(str_ss(result_types[self.success]), 'darkslategrey', '#eef5f5') +  results_html + str_italic(self._caveats()) + effect_md)


# ### Dice Functions

# In[109]:


_last_roll = None

def roll_action (trait=0, mod=0, move=None):
    global _last_roll
    
    if type(trait) == int or type(trait) == float:
        roll_trait = ("", int(trait), None)
    
    elif type(trait) == str and hasattr(pc, trait):
        attr = getattr(pc, trait)
        roll_trait = (attr.label, int(attr.value), pc)
    
    elif type(trait) == Stat or type(trait) == StatMeter:
        roll_trait = (trait.label, int(trait.value), trait._owner)
    
    else:
        printmd("*Use a number, a stat belonging to a player character/asset, or edge|heart|iron|shadow|wits|health|spirit|supply.*")
        return
    
    _last_roll = _roll(move=move, mod=mod, trait=roll_trait)
            
    display(_last_roll)

action_roll = roll_action


# In[110]:


def roll_progress (target, move=None):    
    global _last_roll
    
    if type(target) == int or type(target) == float:
        roll_target = ("", int(target))
    
    elif issubclass(type(target), ProgressMeter):
        roll_target = (target.label, int(target.value))
    
    else:
        printmd("*Use a number or a progress meter with this function.*")
        return
    
    
    _last_roll = _roll(move=move, progress_target=roll_target)

    display(_last_roll)
    
progress_roll = roll_progress


# In[111]:


def reroll (action = -1, c1= -1, c2 = -1):
    if _last_roll == None:
        printmd("*No roll has been made.*")
        return
    
    if action == -1 and c1 == -1 and c2 == -1:
        printmd("*Set action, c1 (for the first challenge die), and/or c2 (second challenge die) to change that die from the previous roll.*")
        return
    
    _last_roll.memo = ""
    
    if not action==-1:
        _last_roll.d6 = action
        _last_roll.memo += f"Set action die to {action}. "
    if not c1==-1:
        _last_roll.c1 = c1
        _last_roll.memo += f"Set first challenge die to {c1}. "
    if not c2==-1:
        _last_roll.c2 = c2
        _last_roll.memo += f"Set second challenge die to {c2}. "
    
    display(_last_roll)


# In[112]:


def burn_momentum (character = None):
    global pc
    global _last_roll
    
    if character == None:
        character = pc
        
    if not isinstance(character, Player_Character):
        printmd("**Must be a Player Character to burn momentum. Or, leave blank to use the default pc.**")
        return
    
    if _last_roll == None:
        printmd("*No roll has been made.*")
        return
    
    if _last_roll.progress_target > 0:
        printmd("*Cannot burn momentum on a progress move.*")
        return

    score = _last_roll.score
    
    c = character
    
    if (_last_roll.c1 >= score and c.momentum >= _last_roll.c1) or (_last_roll.c2 >= score and c.momentum >= _last_roll.c2):
        _last_roll._momentum_override = c.momentum.value
        _last_roll.memo = f"Burned momentum. Score is now set to {c.momentum.value}."
        
        c.momentum.reset()
        
        display(_last_roll)
        
    else:
        printmd("*Burning momentum would be pointless.*")


# In[ ]:





# ## Moves
# 
# Moves are passed around as dictionary entries with the keys: "Category" "Text" "Strong" "Weak" "Miss"

# In[ ]:





# In[113]:


class _Moves(_CategoryBin):
    
        
    def __init__(self):
        
        self._desc = "Moves"
        
        with open(PATH + "Data/starforged_moves_drek.json", "r") as _file:
            self._data = json.load(_file)
        
        categories = defaultdict(list)
        
        for move, move_data in self._data.items():
            categories[move_data["Category"]].append(move)
            
            if move_data["Kind"] == "No Roll":
                move_obj = _item_template(self, move)
            elif move_data["Kind"] == "Action":
                move_obj = self._move_action(self, move)
            else:
                move_obj = self._move_progress(self, move)
                
            setattr(self, _convert_label_to_attr_str(move), move_obj)
            
        self._categories = categories
    
        super().__init__()
    
    def _print_item (self, item):
        printmd(str_textbox(str_emphasis(item.title()) + "\n\n" + self._data[item]["Text"]))
    
    def _do (self, item, trait=None, mod=0, progress=False):
        if trait==None and mod==0:
            self._print_item(item)
            return
        else:
            if trait==None:
                trait=0
            if progress:
                roll_progress(trait, self._data[item])
            else:
                roll_action(trait, mod, self._data[item])
        
    class _move_action(_item_template):
        def __call__(self, trait=None, mod = 0):
            self.parent._do(self.name, trait, mod)
        
    class _move_progress(_item_template):
        def __call__(self, progress=None):
            self.parent._do(self.name, progress, progress=True)

    class _move_category():
        
        def __init__(self, parent, name, moves_list):
            self._parent = parent
            self._name = name
            for move in moves_list:
                attr = _convert_label_to_attr_str(move)
                reference = getattr(parent, attr)
                setattr(self, attr, reference)
                
        def __call__(self):
             self._parent.list(self._name)
        
        def _ipython_display_(self):
            self()
            
move = _Moves()


# In[ ]:





# ## Testing Playground

# In[ ]:





# In[ ]:





# In[ ]:




