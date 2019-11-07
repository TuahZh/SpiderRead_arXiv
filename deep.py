#!/usr/bin/env python
# coding: utf-8

# In[1]:


from papers import *
from ads import *


# In[2]:


my_p = PaperExt(ads_id="2015ApJ...799..103Z")
print(my_p)


# In[ ]:


lp_ads = ListPapersExt()
t0 = time.time()
#lp_deep = lp_ads.dig_deep(my_p, nap=pl_nap(time.time()-t0, 5.), deep=2, only='citation')
lp_deep = lp_ads.dig_deep(my_p, nap=10., deep=2, only='citation')


# In[ ]:


with open("deep_tmp.pkl", "wb") as f:
    pck.dump(lp_deep, f)


# In[ ]:


lp_deep.summary()


# In[ ]:


for a in []:
    print("some")


# In[ ]:




