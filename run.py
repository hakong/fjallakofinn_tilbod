import csv
import multiprocessing as mp

from time import time
from simple_get import simple_get
from bs4 import BeautifulSoup as BS


def clean(text):
    return text.replace('\n','').strip().encode('utf-8')


def get(product, target, attr=None):
    try:
        if attr is not None:
            return clean(product.select_one(target).attrs[attr])
        else:
            return clean(product.select_one(target).text)
    except BaseException, ex:
        return ""


def get_product(product_path, page_id):
    html = BS(simple_get(product_path), 'html.parser')
    product = html.select_one('.product-essential')

    item = {
        'path': product_path,
        'image': get(product, '.product-image img', 'src'),
        'name': get(product, '.product-name'),
        'barcode': get(product, '.barcode'),
        'discount': get(product, '.badge'),
        'old_price': get(product, '.old-price .price').split('  ')[-1],
        'new_price': get(product, '.special-price .price').split('  ')[-1]
    }

    # Let'shope only warehouses have statuses
    for warehouse in product.select('.status'):
        if 'available' in warehouse.attrs['class']:
            item[clean(warehouse.text)] = "available"
        else:
            item[clean(warehouse.text)] = "soldout"

    return item


def get_product_list(path, products, page_id):
    print("Working on {} ...".format(page_id))
    html = BS(simple_get(path), 'html.parser')
    times = []
    for anchor in html.select('.category-products .item .actions a'):
        start_time = time()
        try:
            product_path = "https://fjallakofinn.is{}".format(anchor.attrs['href'].encode('utf-8'))
            products.append(get_product(product_path, page_id))
        except BaseException, ex:
            print("FAILED TO GET \n{} :: {}".format(
                anchor.attrs['href'].encode('utf-8'), ex.message)
            )
        times.append(time()-start_time)
    print("{} is  DONE!\n    Average time: {:4.0f}s\n    Total time: {:4.0f}".format(
        page_id, sum(times)/len(times), sum(times)))
    return products


def get_products(path, products):
    html = BS(simple_get(path), 'html.parser')

    last_page_href = html.select('.pagination li')[-1].select_one('a').attrs['href']
    last_page = int(last_page_href.split('page=')[-1])

    processes = []
    for page in range(1, last_page + 1):
        path_with_page = "{}?page={}".format(path, page)
        processes.append(
            mp.Process(target=get_product_list,
                       args=(path_with_page, products, page)
            )
        )

    for p in processes:
        p.start()

    for p in processes:
        p.join()


# path = "https://fjallakofinn.is/is/product/micron-karabinur-large"
# import pdb; pdb.set_trace()
# get_product(path)

if __name__ == "__main__":
    filename = "products.csv"
    path = "https://fjallakofinn.is/is/products/tilbod"
    products = mp.Manager().list()
    start_time = time()
    get_products(path, products)
    print("TOTAL TIME :: {}".format(time() - start_time))

    with open(filename, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, products[0].keys())
        writer.writeheader()
        for product in products:
            writer.writerow(product)
