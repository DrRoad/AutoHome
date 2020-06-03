import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import webbrowser
import numpy as np

st.title("Notre maison en Bretagne")
st.header("Resultats")
st.markdown("---")

st.sidebar.title("Filtres")

vue_mer = st.sidebar.checkbox("Vue Mer", ["Oui", "Non"])
min_budg = st.sidebar.slider("Budget min", 0, 600000, 200000, 10000)
max_budg = st.sidebar.slider("Budget max", 0, 600000, 390000, 10000)
trier_par = st.sidebar.selectbox("Trier par", ["Date", "Score", "Prix décroissant", "Prix croissant", "Taille de maison décroissante", "Taille de terrain décroissante"])

annual_left = 41000

st.sidebar.markdown("---")

st.sidebar.title("Emprunt")

apport = st.sidebar.text_input("Montant apport", 0)
remb = st.sidebar.slider("Période de remboursement", 5, 30, 25, 5)
interet = st.sidebar.text_input("Taux d'intérêt", 0.016)

def compute_remboursement(price):
    to_pay = (price*1.073 + 15000) -int(apport)
    nb_ann = ((1+float(interet))**int(remb)-1)/float(interet)
    ann = to_pay/int(remb)*nb_ann/int(remb)
    return ann/12

def compute_score(size_house, max_size, size_terrain, max_terrain, vue_mer):
    if vue_mer == "Oui":
        return size_house / max_size * size_terrain / max_terrain * (1 + 0.3)
    else:
        return size_house / max_size * size_terrain / max_terrain

def treguet():
    
    URL = 'http://www.cabinet-treguer.fr/advanced-search/page/1/?bedrooms&keyword=29160&max-area&max-price&min-area&status=vente&type=maison'
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')

    num_pg = []
    for val in soup.find(class_="pagination-main").text:
        if val.isdigit():
            num_pg.append(int(val))

    num_pg = max(num_pg)
    res  = []
    
    for npage in range(1, num_pg+1):
        
        URL = 'http://www.cabinet-treguer.fr/advanced-search/page/%s/?bedrooms&keyword=29160&max-area&max-price&min-area&status=vente&type=maison'%str(npage)
        page = requests.get(URL)
        soup = BeautifulSoup(page.content, 'html.parser')
    
        results = soup.find_all(class_="btn btn-primary")
        results = results[::2]

        for val in results:


            link = val['href']
            page = requests.get(link)
            soup = BeautifulSoup(page.content, 'html.parser')

            place = soup.find(id="annonce-description")
            city = place.text.strip().split("–")[-1].split()[0].title()

            pic = soup.find_all(class_="sp-image")

            list_pics = []

            for p in pic:
                list_pics.append(p['src'])

            results2 = soup.find_all(class_="text-right")

            price = int(soup.find("strong").text.replace(" €", "").replace(".", ""))
            vue_mer = soup.find(id="descriptionblockxs").text

            to_ret = "Non"

            if ("vue" in vue_mer or "bord" in vue_mer or "accès" in vue_mer) and ("mer" in vue_mer or "grève" in vue_mer or "baie" in vue_mer):
                to_ret="Oui"

            feat = []
            for elem in results2[:4]:
                if str(elem.text) != "":
                    feat.append(int(elem.text.replace(" m²", "")))

            feat.append(price)
            feat.append(city)
            feat.append(link)
            feat.append(list_pics)
            feat.append(to_ret)

            res.append(feat)
    df=pd.DataFrame(res)
    df.columns=["Surface", "Terrain", "Chambres", "Prix", "Ville", "Lien", "Photos", "VueMer"]
    df['Site'] = "Treguer"
    df['Couverture'] = df['Photos'].apply(lambda x: x[0])
    
    df = df.reindex(['Prix', 'Ville', 'Surface', 'Chambres', 'Couverture', 'Lien',
       'Terrain', 'Photos', 'VueMer', 'Site'], axis=1)

    return df

def bourse_immo():

    link = "https://www.bourse-immobilier.fr/achat-maison-crozon?quartiers=29042&surface=0&sterr=0&prix=-&typebien=1&nbpieces=1-2-3-4-5&og=0&where=Crozon-__29160_&_b=1&_p=0&tyloc=2&neuf=1&ancien=1&ids=29042"

    page = requests.get(link)
    soup = BeautifulSoup(page.content, 'html.parser')

    fix = "https://www.bourse-immobilier.fr"

    all_res = []

    for l in soup.find_all(class_="bottom"):
        lk = l.find("a", href=True)['href']
        if "annonce" in lk:
            new_link = fix + lk
            
            page = requests.get(new_link)
            soup2 = BeautifulSoup(page.content, 'html.parser')
            
            surf = None
            terr = None
            chb = None
            price = None
            ville = None
            pic = None
            
            pr = soup2.find(id="detailprix").text
            price = int(pr.split(" : ")[1].split("-")[0].strip().replace("€", "").replace(" ", ""))
            city = soup2.find(class_="ville").text.split("|")[0].strip()
            
            pics = soup2.find_all(class_="img-responsive")
            pic_fix = "https://www.bourse-immobilier.fr/jpg/"
            list_p = []
            
            descr = soup2.find(id="visitez").text
            
            vue_mer = "Non"
            if ("vue" in descr or "bord" in descr or "accès" in descr) and ("mer" in descr or "grève" in descr or "baie" in descr):
                vue_mer = "Oui"
                    
            for p in pics:
                list_p.append(p['data-lazy'])
            
            for char in soup2.find(id="caracteristique-bien").find_all("li"):
                
                if "Surface habitable" in str(char):
                    surf = int(char.text.split(":")[1].strip().replace("m²", "").strip().replace(" ", ""))
                elif "Superficie terrain" in str(char):
                    terr = int(char.text.split(":")[1].strip().replace("m²", "").strip().replace(" ", ""))
                elif "Chambre(s)" in str(char):
                    chb = int(char.text.split(":")[1].strip().replace("m²", "").strip().replace(" ", ""))
                    
            all_res.append([price, surf, terr, chb, new_link, city, list_p, vue_mer])
        
    df = pd.DataFrame(all_res)
    print(df)
    
    df.columns=["Prix", "Surface", "Terrain", "Chambres", "Lien", "Ville", "Photos", "VueMer"]
    df['Site'] = "BourseImmo"
    df['Couverture'] = df['Photos'].apply(lambda x: x[0])

    df = df.reindex(['Prix', 'Ville', 'Surface', 'Chambres', 'Couverture', 'Lien',
       'Terrain', 'Photos', 'VueMer', 'Site'], axis=1)
    return df
    
def ouest_france():
    
    def find_price(val):
        return int(val.find(class_="annPrix").text.strip().replace("\xa0", "").replace(" ", "").replace("€", ""))

    def find_city(val):
        return val.find(class_="annVille").text.title()

    def find_crit(val):
        return val.find(class_="annCriteres").text.strip()

    URL = 'https://www.ouestfrance-immo.com/acheter/maison/?lieux=12982,12984,13060,13176,12983,12959&vueMer=1'
    page = requests.get(URL)
    
    soup = BeautifulSoup(page.content, 'html.parser')
    results= soup.find(id="blocListAnnonces")
    bloc_res = results.find_all(class_='annLink')
    fix='https://www.ouestfrance-immo.com'
    
    all_val = []

    for val in results.find_all(class_='annLink', href=True):
        my_list = []

        my_list.append(find_price(val))
        my_list.append(find_city(val))
        crit = find_crit(val)
        surf=int(crit.split("|")[0].replace("m² ", ""))
        chb=int(crit.split("|")[1].replace("chb", ""))
        #sdb=crit.split("|")[2].replace("sdb", "")

        my_list.append(surf)
        my_list.append(chb)
        #my_list.append(sdb)

        my_list.append(val.find('img')['data-original'])
        my_list.append(fix+val['href'])

        page = requests.get(fix+val['href'])
        soup = BeautifulSoup(page.content, 'html.parser')
        results2 = soup.find_all('ul')

        terrain = soup.find_all('li')
        for val in terrain:

            if "Surf. terrain" in str(val):
                val = int(str(val).split("<strong>")[1].split("</strong>")[0].replace("m²", "").strip().replace(" ", ""))
                my_list.append(val)

        photos=results2[6]

        list_photos = []

        for pic in photos:
            if pic != '\n':
                list_photos.append(str(pic).split("src=")[1].split(" title=")[0].replace('"',""))
        my_list.append(list_photos)
        all_val.append(my_list)
    
    df_of = pd.DataFrame(all_val)
    df_of.columns=["Prix", "Ville", "Surface", "Chambres", "Couverture", "Lien", "Terrain", "Photos"]
    df_of['VueMer'] = "Oui"
    df_of['Site'] = "OuestFrance"
    
    return df_of

def agence_presquile():

    URL = 'https://www.agencedelapresquile.com/achat-immobilier-crozon/type-1-maison/'
    page = requests.get(URL)

    soup = BeautifulSoup(page.content, 'html.parser')
    results= soup.find_all(class_="btn btn-default")

    fix = "https://www.agencedelapresquile.com"
    all_val = []

    for i in range(1, int(results[1].text)+1):

        URL = 'https://www.agencedelapresquile.com/achat-immobilier-crozon/type-1-maison/'+str(i)
        page = requests.get(URL)

        soup = BeautifulSoup(page.content, 'html.parser')

        results= soup.find_all(class_="block-link")
        link_thumbnail = list(soup.find_all(class_="mainImgLst3"))

        k = 0

        for link in results:

            page = requests.get(fix+link['href'])
            soup = BeautifulSoup(page.content, 'html.parser')
            results2 = soup.find_all(class_="data")

            photos = soup.find_all("img")
            link_photos = []
            for pic in photos:
                if ".jpg" in str(pic) and 'alt=""' in str(pic):
                    link_photos.append("http://" + pic['src'][2:])

            values = []

            prix = None
            ville = None
            surf = None
            chb = None
            terr = None

            for info in results2:

                if "Prix du bien" in str(info):
                    prix = int(info.find(class_="valueInfos").text.replace("€", "").strip().replace(" ", ""))
                elif "Ville" in str(info):
                    ville = info.find(class_="valueInfos").text.strip().title()
                elif "Surface habitable (m²)" in str(info):
                    surf = int(info.find(class_="valueInfos").text.replace("m²", "").strip().replace(" ", ""))
                elif "Nombre de chambre(s)" in str(info):
                    chb = int(info.find(class_="valueInfos").text.strip())
                elif "surface terrain" in str(info):
                    terr = int(info.find(class_="valueInfos").text.replace("m²", "").strip().replace(" ", ""))

            a_vue_mer = "Non"
            vue_mer = soup.find(itemprop="description").text
            if ("vue" in vue_mer or "bord" in vue_mer or "accès" in vue_mer) and ("mer" in vue_mer or "grève" in vue_mer or "baie" in vue_mer):
                a_vue_mer = "Oui"

            all_val.append([prix, ville, surf, chb, "http://" +link_thumbnail[k]['src'][2:], fix+link['href'], terr, link_photos, a_vue_mer])
            k += 1
    df_pi = pd.DataFrame(all_val)
    df_pi.columns=["Prix", "Ville", "Surface", "Chambres", "Couverture", "Lien", "Terrain", "Photos", "VueMer"]
    df_pi['Site'] = "PresquileImmo"
    
    return df_pi

if st.sidebar.button("Actualiser"):
    df_of = ouest_france()
    df_of['order'] = range(len(df_of))
    df_pi = agence_presquile()
    df_pi['order'] = range(len(df_pi))
    df_concat = pd.concat([df_of, df_pi])
    df_treguet = treguet()
    df_treguet['order'] = range(len(df_treguet))
    df_concat = pd.concat([df_concat, df_treguet])
    df_immo = bourse_immo()
    df_immo['order'] = range(len(df_immo))
    df_concat = pd.concat([df_concat, df_immo])

    df_concat['score'] = df_concat.apply(lambda x: compute_score(x['Surface'], max(df_concat['Surface']), x['Terrain'], max(df_concat['Terrain']), x['VueMer']), axis=1)

    df_concat["Remboursement"] = df_concat['Prix'].apply(lambda x:compute_remboursement(x))
    df_concat.to_csv("df.csv")
else:
    df_concat = pd.read_csv("df.csv")

if trier_par == "Prix décroissant":
	df_concat = df_concat.sort_values(by="Prix", ascending=False)
elif trier_par == "Prix croissant":
	df_concat = df_concat.sort_values(by="Prix", ascending=True)
elif trier_par == "Taille de maison décroissante":
	df_concat = df_concat.sort_values(by="Surface", ascending=False)
elif trier_par == "Taille de terrain décroissante":
	df_concat = df_concat.sort_values(by="Terrain", ascending=False)
elif trier_par == "Date":
    df_concat = df_concat.sort_values(by="order", ascending=True)
elif trier_par == "Score":
    df_concat = df_concat.sort_values(by="score", ascending=False)
elif trier_par == "Remboursement":
    df_concat = df_concat.sort_values(by="Remboursement", ascending=False)

if vue_mer:
	df_concat=df_concat[df_concat["VueMer"]=="Oui"]

df_concat=df_concat[df_concat["Prix"]>= min_budg]
df_concat=df_concat[df_concat["Prix"]<= max_budg]

for val in df_concat.iterrows():
	if val[1]['VueMer']=="Oui":
		st.subheader("Maison vue Mer à %s de %s m² sur terrain de %s m²"%(val[1]['Ville'], val[1]['Surface'], val[1]['Terrain']))
	else:
		st.subheader("Maison à %s de %s m² sur terrain de %s m²"%(val[1]['Ville'], val[1]['Surface'], val[1]['Terrain']))
	st.write(" ")
	st.write("Prix: ", val[1]['Prix'], " €, soit ", np.round(int(val[1]['Remboursement'])), " €/mois")
	st.write("Ville: ", val[1]['Ville'])
	st.write("Surface: ", val[1]['Surface'])
	st.write("Terrain: ", val[1]['Terrain'])
	st.write("Chambres: ", val[1]['Chambres'])
	st.markdown("Lien: [%s](%s)"%(val[1]['Site'], val[1]['Lien']))
	st.image(val[1]['Couverture'], width=500)
	if st.checkbox("Voir photos", key=val):
		for p in val[1]['Photos']:
			st.image(p, width=500)
	st.markdown("---")


st.write(df_concat)