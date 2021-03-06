from datetime import datetime

from django.shortcuts import render, redirect, render_to_response

from rango.models import Category, Page

from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm

from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User


from rango.bing_search import run_query


def index(request):

    category_list = Category.objects.order_by('-likes')[:5]
    page_list = Page.objects.order_by('-views')[:5]

    context_dict = {'categories': category_list, 'pages': page_list}

    visits = request.session.get('visits')
    if not visits:
        visits = 1
    reset_last_visit_time = False

    last_visit = request.session.get('last_visit')
    if last_visit:
        last_visit_time = datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")

        if (datetime.now() - last_visit_time).seconds > 0:
            # ...reassign the value of the cookie to +1 of what it was before...
            visits = visits + 1
            # ...and update the last visit cookie, too.
            reset_last_visit_time = True
    else:
        # Cookie last_visit doesn't exist, so create it to the current date/time.
        reset_last_visit_time = True

    if reset_last_visit_time:
        request.session['last_visit'] = str(datetime.now())
        request.session['visits'] = visits
    context_dict['visits'] = visits


    response = render(request,'rango/index.html', context_dict)

    return response


def about(request):
    context_dict = {'boldmessage': "This is the about page!"}
    return render(request, 'rango/about.html', context_dict)

def category(request, category_name_slug):
    context_dict = {'category_name_slug':category_name_slug}
    context_dict['result_list'] = None
    context_dict['query'] = None
    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
            result_list = run_query(query)

            context_dict['result_list'] = result_list
            context_dict['query'] = query
    
    try:
        #can we find a category name slug with the given name?
        #If we can't, the get() method raises a DoesNotExist exception
        #So the .get() method returns one model instance or raises an exception.
        category = Category.objects.get(slug=category_name_slug)
        context_dict['category_name']=category.name
        context_dict['category_name_slug']=category_name_slug


        #Get all associated pages
        #note that filter returns >=1 model instances
        pages = Page.objects.filter(category=category).order_by('-views')

        #Adds results list to the template context under name pages.
        context_dict['pages'] = pages
        #Also add category object from the database to the cont dict
        #this is to verify it exists
        context_dict['category'] = category
        
    except Category.DoesNotExist:
        #Don't do anything, the template displays the "no category" message
        pass

    if not context_dict['query']:
        context_dict['query'] = category.name
    categories = Category.objects.order_by('-likes')[:5]
    context_dict['categories'] = categories
    return render(request, 'rango/category.html', context_dict)

@login_required
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

@login_required
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

def register(request):

    #if request.session.test_cookie_worked():
    #   print ">>> TEST COOKIE WORKED!"
    #    request.session.delete_test_cookie()
    # A boolean value for telling whethert the reg. was successful
    # Set to false initially. Change to true upon completion.
    registered = False

    #If http post, we need to process the form
    if request.method == 'POST':
        # attempt to grab info from raw form info
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data = request.POST)

        #if forms are valid...
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user

            #did they supply picture?
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']
                
            #now we save the user profile instance
            profile.save()

            #update the variable to indicate success
            registered = True
        
        else:
            print user_form.errors, profile_form.errors

    else:
        user_form = UserForm()
        profile_form =  UserProfileForm()
    return render(request, 'rango/register.html',
                  {'user_form':user_form, 'profile_form':profile_form, 'registered':registered})

def user_login(request):
    
    #if the request is an http request, pull relevant info
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        #try to validate given userinfo
        user = authenticate(username=username, password=password)
        # if we have a user object the details are correct
        # otherwise we will get None
        if user:
            # is the account active (e.g. not disabled)
            if user.is_active:
                #now we can try to log them in
                login(request, user)
                return HttpResponseRedirect('/rango/')
            else:
                #an inactive user
                return HttpResponse("Your Rango account is disabled")
        else:
            if User.objects.filter(username=username).exists():
                error_msg = "Invalid password supplied."
            #bad login info was given
            else:
                error_msg = "Invalid username supplied."
            return render(request, 'rango/login.html', {'error_msg':error_msg, 'username':username})
    else:
        #else this user hasn't attempted to login yet, i.e. the 
        #request method was a "GET"
        return render(request, 'rango/login.html', {})

@login_required
def user_logout(request):
    #makes use of imported logout. since decorator
    #will insist that the user is logged in, this makes sense.
    logout(request)
    return HttpResponseRedirect('/rango/')


@login_required
def restricted(request):
    return render(request, 'rango/restricted.html', {})


'''
def search(request):
    
    result_list = []

    if request.method=='POST':
        query = request.POST['query'].strip()

        if query:
            #run bing function to get results
            result_list = run_query(query)
        else:
            result_list = ["No Results"]

    return render(request, 'rango/search.html', {'result_list':result_list})
'''

def track_url(request):
    if request.method == 'GET':
        if 'page_id' in request.GET:
            page_id = request.GET['page_id']
            page = Page.objects.get(id=page_id)
            page.views += 1
            page.save()
            page_url = page.url
            return redirect(page_url, {'page':page})
        else:
            return HttpResponse("page does not exist")
    else:
        return render(request, 'rango/')
    
from django.contrib.auth.decorators import login_required
    
@login_required
def like_category(request):

    cat_id = None
    if request.method == 'GET':
        cat_id = request.GET['category_id']

    likes = 0
    if cat_id:
        cat = Category.objects.get(id=int(cat_id))
        if cat:
            likes = cat.likes + 1
            cat.likes =  likes
            cat.save()

    return HttpResponse(likes)

def get_category_list(max_results=0, starts_with=''):
    cat_list = []
    if starts_with:
        cat_list = Category.objects.filter(name__istartswith=starts_with)

    if max_results > 0:
        if len(cat_list) > max_results:
            cat_list = cat_list[:max_results]

    return cat_list

def suggest_category(request):

    cat_list = []
    starts_with = ''
    if request.method == "GET":
        starts_with = request.GET['suggestion']

    cat_list = get_category_list(8, starts_with)

    empty = (starts_with == '')
    
    return render(request, 'rango/category_list_search.html', {'cat_list':cat_list, 'empty':empty})


@login_required
def auto_add_page(request):
    context = RequestContext(request)
    context_dict = {}
    cat_id = None
    url = None
    title = None
    
    if request.method == "GET":
        title = request.GET['title']
        url = request.GET['url']
        cat_id = request.GET['category_id']
        print(title, url, cat_id)
        print("HEYYY")
        if cat_id:
            print("CHECK")
            category = Category.objects.get(id=int(cat_id))
            p = Page(title=title, url=url, category=category)
            p.save()
            pages = Page.objects.filter(category = category).order_by('-views')
            context_dict['pages'] = pages
            print("DUDE")
    else:
        pass

    return render(request, 'rango/page_list.html', context_dict, context)

        
            
