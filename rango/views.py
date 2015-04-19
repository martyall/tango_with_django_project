from django.shortcuts import render
from rango.models import Category, Page
from rango.forms import CategoryForm, PageForm

def index(request):
    category_list = Category.objects.order_by('-likes')[:5]
    category_list_views = Category.objects.order_by('-views')[:5]
    context_dict = {'categories':category_list,'categories_views':category_list_views}
    return render(request, 'rango/index.html', context_dict)

def about(request):
    context_dict = {'boldmessage': "This is the about page!"}
    return render(request, 'rango/about.html', context_dict)

def category(request, category_name_slug):
    context_dict = {'category_name_slug':category_name_slug}

    try:
        #can we find a category name slug with the given name?
        #If we can't, the get() method raises a DoesNotExist exception
        #So the .get() method returns one model instance or raises an exception.
        category = Category.objects.get(slug=category_name_slug)
        context_dict['category_name']=category.name
        context_dict['category_name_slug']=category_name_slug


        #Get all associated pages
        #note that filter returns >=1 model instances
        pages = Page.objects.filter(category=category)

        #Adds results list to the template context under name pages.
        context_dict['pages'] = pages
        #Also add category object from the database to the cont dict
        #this is to verify it exists
        context_dict['category'] = category
        
    except Category.DoesNotExist:
        #Don't do anything, the template displays the "no category" message
        pass
        
    return render(request, 'rango/category.html', context_dict)

def add_category(request):
    # A HTTP POST?
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        # Have we been provided with a valid form?
        if form.is_valid():
            # Save the new category to the database.
            form.save(commit=True)

            # Now call the index() view.
            # The user will be shown the homepage.
            return index(request)
        else:
            # The supplied form contained errors - just print them to the terminal.
            print form.errors
    else:
        # If the request was not a POST, display the form to enter details.
        form = CategoryForm()

    # Bad form (or form details), no form supplied...
    # Render the form with error messages (if any).
    return render(request, 'rango/add_category.html', {'form': form})

def add_page(request, category_name_slug):

    # need some category to exist for this page
    try:
        cat = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
        cat = None

    #an http post? if so need to process it
    #if not, we're going to be filling out a blank form
    if request.method == 'POST':
        form = PageForm(request.POST)
        #check to see if form was filled out properly
        #if so, send to db and return to index
        #if not, print the errors
        if form.is_valid():
            if cat:
                page = form.save(commit=False)
                page.category = cat
                page.views = 0
                page.save()
                return category(request, category_name_slug)
        else:
            print form.errors
    #if it wasn't a post request, give the blank form
    else:
        form = PageForm()
    context_dict = {'form':form, 'category':cat, 'category_name_slug':category_name_slug}
    return render(request, 'rango/add_page.html', context_dict)
