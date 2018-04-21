from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes, authentication_classes

def validateRequest(request, keys, method):
    """
        Validates that a request has the correct keys
        :param keys
            [ string ] --> list of keys
        :param request
            Request object
        :param method
            string --> 'GET' or 'POST'
        
        :return bool
    """
    result = True

    d = request.POST if method == 'POST' else request.GET

    for key in keys:
        result = result and (key in d)
    
    return result


@require_POST
def signUp(request):
    """
        Sign Up for JetsonBenefits
        :param request 
            { POST: { firstName: string, lastName: string, email: string, password: string } }

        :return JsonResponse
            { success: bool, token: string, error: string }

    """
    requiredKeys = ['firstName', 'lastName', 'email', 'password']
    res = { 'success': False, 'error': '', 'token': '' }

    if (validateRequest(request, requiredKeys, 'POST')):
        firstName = request.POST['firstName']
        lastName = request.POST['lastName']
        email = request.POST['email']
        password = request.POST['password']

        # check if user has already been created
        if User.objects.filter(username=email).exists():
            res['success'] = False
            res['error'] = 'Existing account already associated with ' + email
            print(res['error'])
        else:
            # create user & api token
            user = User.objects.create_user(username=email, email=email, password=password)
            token = Token.objects.create(user=user)
            res['success'] = True
            res['token'] = token.key
            print('created user: ' + username)

    else:
        res['success'] = False
        res['error'] = 'Invalid POST args'

    return JsonResponse(res)


@require_POST
def signIn(request):
    """
        Sign In for JetsonBenefits
        :param request 
            { POST: { username: string, password: string } }

        :return JsonResponse
            { success: bool, token: string, error: string }

    """
    requiredKeys = ['username', 'password']
    res = { 'success': False, 'error': '', 'token': '' }

    if (validateRequest(request, requiredKeys, 'POST')):
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        # check if user has already been created
        if user is None:
            res['success'] = False
            res['error'] = 'Incorrect username and password combination'
        else:
            print('authenticated user: ' + username)
            # retrieve api token
            token = Token.objects.get(user=user)
            if token is not None:
                res['success'] = True
                res['token'] = token.key
            else:
                res['success'] = False
                res['error'] = 'No token exists for user'

    else:
        res['success'] = False
        res['error'] = 'Invalid POST args'

    return JsonResponse(res)


@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def updateUserInfo(request):
    """
        Update a users information
        :param request
            { POST: { userData: object } }

        :return JsonResponse
            { success: bool, error: string }
    """
    requiredKeys = ['userData']
    res = { 'success': False, 'error': '' }

    if (validateRequest(request, requiredKeys, 'POST')):
        user = request.user
        # -- fetch from USER table here
        # -- update corresponding fields
        res['success'] = True
    else:
        res['success'] = False
        res['error'] = 'Invalid request args'
    
    return JsonResponse(res)


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def getUserInfo(request):
    """
        Get a users information
        :param request:
        
        :return JsonResponse
            { success: bool, error: string, data: object }
    """
    requiredKeys = []
    res = { 'success': False, 'error': '', data: None }

    if (validateRequest(request, requiredKeys, 'GET')):
        user = request.user
        # -- retrieve fields
        #-- add data to res['data']
        res['success'] = True
    else:
        res['success'] = False
        res['error'] = 'Invalid request args'

    return JsonResponse(res)


@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def updateInsuranceInfo(request):
    """
        Update insurance info for a user
        :param request:

        :return JsonResponse
            { success: bool, error: string }
    """
    requiredKeys = []
    res = { 'success': False, 'error': '' }

    if (validateRequest(request, requiredKeys, 'POST')):
        user = request.user
        # -- get information from POST request
        # -- make updates
        res['success'] = True
    else:
        res['success'] = False
        res['error'] = 'Invalid request args'
    
    return JsonResponse(res)


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def getInsuranceInfo(request):
    """
        Gets insurance info for a user
        :param request:

        :return JsonResponse
            { success: bool, error: string, data: object }
    """
    requiredKeys = []
    res = { 'success': False, 'error': '', data: None }

    if (validateRequest(request, requiredKeys, 'GET')):
        user = request.user
        # -- get data
        # -- add data to res['data']
        res['success'] = True
    else:
        res['success'] = False
        res['error'] = 'Invalid request args'
    
    return JsonResponse(res)


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def getAllInsuranceInfo(request):
    """
        Gets all insurance info for a user
        :param request:

        :return JsonResponse
            { success: bool, error: string, data: object }
    """
    requiredKeys = []
    res = { 'success': False, 'error': '', data: None }

    if (validateRequest(request, requiredKeys, 'GET')):
        user = request.user
        # -- get data
        # -- add data to res['data']
        res['success'] = True
    else:
        res['success'] = False
        res['error'] = 'Invalid request args'
    
    return JsonResponse(res)


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def getInsuranceQuote(request):
    """
        Get insurance quote for a user
        :param request:

        :return JsonResponse
            { success: bool, error: string, data: object }
    """
    requiredKeys = []
    res = { 'success': False, 'error': '', data: None }

    if (validateRequest(request, requiredKeys, 'GET')):
        user = request.user
        # -- get data
        # -- add data to res['data']
        res['success'] = True
    else:
        res['success'] = False
        res['error'] = 'Invalid request args'
    
    return JsonResponse(res)


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def getAllInsuranceQuotes(request):
    """
        Gets all insurance quotes for a user
        :param request:

        :return JsonResponse
            { success: bool, error: string, data: object }
    """
    requiredKeys = []
    res = { 'success': False, 'error': '', data: None }

    if (validateRequest(request, requiredKeys, 'GET')):
        user = request.user
        # -- get data
        # -- add data to res['data']
        res['success'] = True
    else:
        res['success'] = False
        res['error'] = 'Invalid request args'
    
    return JsonResponse(res)


@api_view(['GET', 'POST']) #TODO: not sure if this is get or post
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def generateInsuranceQuotes(request):
    """
        Generates insurance quotes for a user
        :param request:

        :return JsonResponse
            { success: bool, error: string, data: object }
    """
    requiredKeys = []
    res = { 'success': False, 'error': '', data: None }

    if (validateRequest(request, requiredKeys, 'GET')):
        user = request.user
        # -- get data
        # -- add data to res['data']
        res['success'] = True
    else:
        res['success'] = False
        res['error'] = 'Invalid request args'
    
    return JsonResponse(res)