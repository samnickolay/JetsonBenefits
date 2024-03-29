from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_GET
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from django.core import serializers


from django.views.decorators.csrf import ensure_csrf_cookie


from app.models import *
import json
from app.scripts.recommendation_logic import *
from django.forms.models import model_to_dict

from api.formatting import *

#TODO: what to output if nothing returned from generating quotes

def validateRequest(request, keys, method, response):
    """
        Validates that a request has the correct keys
        :param keys
            [ string ] --> list of keys
        :param request
            Request object
        :param method
            string --> 'GET' or 'POST'
        
        :return bool
            --> Note: updates response object passed in to set success and error messages
    """
    result = True

    d = request.POST.dict() if method == 'POST' else request.GET.dict()

    for key in keys:
        result = result and (key in d)
    
    # if incorrect args, update the response object and set status_code to an error code
    if not result:
        response['sucess'] = False
        response['error'] = 'Invalid ' + method + ' arguments'
        response['status_code'] = 500

    return result

def asInt(value):
    return 0 if value == '' else int(value)

@require_POST
def signup(request):
    """
        Sign Up for JetsonBenefits
        :param request 
            { POST: { firstName: string, lastName: string, email: string, password: string } }

        :return JsonResponse
            { success: bool, token: string, error: string }

    """
    requiredKeys = ['firstName', 'lastName', 'email', 'password']
    res = { 'success': False, 'error': '', 'token': '' }

    if (validateRequest(request, requiredKeys, 'POST', res)):
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
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=firstName,
                last_name=lastName
            )
            token = Token.objects.create(user=user)
            res['success'] = True
            res['token'] = token.key
            print('created user: ' + user.username)

    return JsonResponse(res)


@require_POST
def login(request):
    """
        Log In for JetsonBenefits
        :param request 
            { POST: { username: string, password: string } }

        :return JsonResponse
            { success: bool, token: string, error: string }

    """
    requiredKeys = ['username', 'password']
    res = { 'success': False, 'error': '', 'token': '' }

    if (validateRequest(request, requiredKeys, 'POST', res)):
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
                res['name'] = user.first_name
            else:
                res['success'] = False
                res['error'] = 'No token exists for user'

    return JsonResponse(res)


@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def updateUserInfo(request):
    """
        Update a users information
        :param request
            { POST: { userData: object } }
            userData = {
                age:  
                zipcode:  
                marital_status: 
                health_condition: 
                annual_income:  
                spouse_annual_income:  
                spouse_age: 
                num_kids:  
                kid_ages:
            }

            kid_ages is an array of ints
            marital status is 'single', 'married', 'divorced' or 'widowed'
            health is 'Excellent', Good', Meh', or Poor'


        :return JsonResponse
            { success: bool, error: string }
    """

    requiredKeys = ['userData']
    res = { 'success': False, 'error': '' }
    if (validateRequest(request, requiredKeys, 'POST', res)):
        user = request.user
        userData = json.loads(request.POST['userData'])
        userData['user_id'] = user
        kid_ages = userData['kid_ages']
        del userData['kid_ages']

        # loop through keys that map to numbers and cast correctly
        numberkeys = ['spouse_annual_income', 'annual_income', 'age', 'num_kids', 'zipcode', 'spouse_age']
        for key in numberkeys:
            if not type(userData[key]) in [int, float]:
                userData[key] = asInt(userData[key])
        
        #save user answers into object
        getAnswers = user_general_answers(**userData)
        getAnswers.save()

        # Delete kids and add new ones instead if any exist
        user_kids.objects.filter(user_id=user).delete()
        i = 0
        while(i<len(kid_ages)):
            age = user_kids(user_id=user, kid_age = asInt(kid_ages[i]), will_pay_for_college = 'yes')
            age.save()
            i = i+1

        res['success'] = True

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
            data = {
                age:,
                annual_income:,
                health:,
                kid_ages: [],
                marital_status:
                num_kids:, 
                spouse_age:,
                spouse_annual_income:,
                zipcode:
            }
    """
    requiredKeys = []
    res = { 'success': False, 'error': '', 'data': None }

    if (validateRequest(request, requiredKeys, 'GET', res)):
        user = request.user

        #get users answers
        user_answers = list(user_general_answers.objects.filter(user_id=user).values())
        userData = {}
        if len(user_answers)>=1:
            userData = user_answers[0]


        #get users kids
        if (user_kids.objects.filter(user_id = user).exists()):
            user_kids_ages = list(user_kids.objects.values_list('kid_age', flat = True).filter(user_id = user))

            userData['kid_ages'] = user_kids_ages
        else:
            userData['kid_ages'] = []

        res['data'] = userData
        res['success'] = True

    return JsonResponse(res)


@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def updateInsuranceInfo(request):
    """
        Update insurance info for a user
        :param request:
            insuranceType = 'HEALTH' | 'LIFE' | 'DISABILITY'

        if insuranceType is HEALTH
        insuranceData = {
                q_1: 'No', 
                q_2: 'No', 
                q_5: 'Might go',
                q_6: 'Never or just for my annual physical', 
                q_7: "Drink some tea, it'll pass", 
                q_8: 'Find out cost before booking appt', 
                q_9: 'It crosses my mind sometimes.', 
                q_10: 'It crosses my mind sometimes.',
                q_11: 'Convenient time with any doctor',
                q_12: 'If my doc says so'
            }
            q_1 is 'Yes' or 'No'
            q_2 is 'Yes' or 'No'
            q_5 is 'No chance', 'Might go', 'I'll definitely go'
            q_6 is '1-3 times besides my physical exam', 'Never or just for my annual physical', or 'More than 3 times a year'
            q_7 is 'More than 3 times a year', 'If I don't feel better in a few days, I'm going to the doctor', or 'Go to the doctor immediately'
            q_8 is 'Do nothing, I feel fine', 'Find out cost before booking appt' or 'Schedule right away'
            q_9 is 'It crosses my mind sometimes.', 'Not a lot.', or 'Huge worry'
            q_10 is 'It crosses my mind sometimes.', 'Not a lot.', or 'Huge worry'
            q_11 is 'I don't...', 'Convenient time with any doctor', or 'Must see my doc'
            q_12 is 'If my doc says so', 'Not likely', or 'I love second opinions'

        if insuranceType is LIFE
        insuranceData = {
            mortgage_balance: 20000,
            other_debts_balance: 500,
            existing_life_insurance:0,
            balance_investings_savings: 1000,
        }

        :return JsonResponse
            { success: bool, error: string }
    """
    requiredKeys = ['insuranceType', 'insuranceData']
    res = { 'success': False, 'error': '' }

    if (validateRequest(request, requiredKeys, 'POST', res)):
        user = request.user
        insuranceType = request.POST['insuranceType']
        insuranceData = json.loads(request.POST['insuranceData'])

        print(insuranceData)

        if (insuranceType == 'HEALTH'):
            healthRecord = user_health_questions_answer(user_id=user)
            
            health_dict = {}
            for key in insuranceData:
                if insuranceData[key] == '':
                    continue
                num = int(key[key.find('_')+1:]) #get id number
                q = health_question_options.objects.get(option = insuranceData[key], health_question_id = num)
                health_dict[key] = q

            # runs over the data in the dictionary returned from health questions options
            for attr, value in health_dict.items():
                setattr(healthRecord, attr, value)
                healthRecord.save()

        elif (insuranceType == 'LIFE'):

            lifeRecord = user_life_answers(user_id=user)
            for attr, val in insuranceData.items():
                if val == '':
                    continue
                setattr(lifeRecord, attr, val)

            lifeRecord.save()

        elif (insuranceType == 'DISABILITY'):
            # DO NOTHING -- disability data already stored
            ### TODO: Is this correct???
            pass

        res['success'] = True
    
    return JsonResponse(res)


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
@require_GET
def getInsuranceInfo(request):
    """
        Gets insurance info for a user
        :param request:
            insuranceType = 'HEALTH' | 'LIFE' | 'DISABILITY'

        :return JsonResponse
            { success: bool, error: string, data: object }
            If insuranceType is HEALTH
            data = {
                q_1:, 
                q_2:, 
                q_5:,
                q_6:, 
                q_7:, 
                q_8:, 
                q_9:, 
                q_10:,
                q_11:,
                q_12:
            }
            q_1 is 'Yes' or 'No'
            q_2 is 'Yes' or 'No'
            q_5 is 'No chance', 'Might go', 'I'll definitely go'
            q_6 is '1-3 times besides my physical exam', 'Never or just for my annual physical', or 'More than 3 times a year'
            q_7 is 'More than 3 times a year', 'If I don't feel better in a few days, I'm going to the doctor', or 'Go to the doctor immediately'
            q_8 is 'Do nothing, I feel fine', 'Find out cost before booking appt' or 'Find out cost before booking appt'
            q_9 is 'It crosses my mind sometimes.', 'Not a lot.', or 'Huge worry'
            q_10 is 'It crosses my mind sometimes.', 'Not a lot.', or 'Huge worry'
            q_11 is 'I don't...', 'Convenient time with any doctor', or 'Must see my doc'
            q_12 is 'If my doc says so', 'Not likely', or 'I love second opinions'

            if a user hasnt answered a question, the value will be ''
            if insuranceType is LIFE
            data = {
                mortgage_balance:,
                other_debts_balance:,
                existing_life_insurance:,
                balance_investings_savings:,
            }
    """
    requiredKeys = ['insuranceType']
    res = { 'success': False, 'error': '', 'data': None }

    if (validateRequest(request, requiredKeys, 'GET', res)):
        user = request.user
        insuranceType = request.GET['insuranceType']
        
        if (insuranceType == 'HEALTH' or insuranceType == 'LIFE' or insuranceType == 'DISABILITY'):
            data = getInsuranceInfoHelper(user, insuranceType)
            res['data'] = data
            res['success'] = True
        else:
            res['error'] = 'invalid insurance type'
    
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

        data = { 
            HEALTH: {
                q_1:, 
                q_2:, 
                q_5:,
                q_6:, 
                q_7:, 
                q_8:, 
                q_9:, 
                q_10:,
                q_11:,
                q_12:
            },
            LIFE: {
                mortgage_balance:,
                other_debts_balance:,
                existing_life_insurance:,
                balance_investings_savings:,
            },
            DISABILITY: {
                annual_income: 10000
            }
        }        
    """
    requiredKeys = []
    res = { 'success': False, 'error': '', 'data': None }

    if (validateRequest(request, requiredKeys, 'GET', res)):
        user = request.user

        health_info = getInsuranceInfoHelper(user, 'HEALTH')
        life_info = getInsuranceInfoHelper(user, 'LIFE')
        disability_info = getInsuranceInfoHelper(user, 'DISABILITY')

        res['data'] = {'HEALTH': health_info, 'LIFE': life_info, 'DISABILITY': disability_info}
        res['success'] = True
    
    return JsonResponse(res)


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def getInsuranceQuote(request):
    """
        Get insurance quote for a user
        :param request:
            insuranceType = 'HEALTH' | 'LIFE' | 'DISABILITY'

        :return JsonResponse
            { success: bool, error: string, data: object }
        if insuranceType is HEALTH
        data = {
            carrier:,
            deductible:,
            deductible_level:,
            has_spouse:,
            health_plan_id:,
            medal:,
            monthly_premium:,
            num_kids:,
            plan_name:,
            plan_type:,
        }

        if insurance type is LIFE
        data = {
            age:,
            carrier:,
            gender:,
            life_plan_id:,
            monthly:
            policy_amount:
            policy_term:
        }
        
        if insurance type is DISABILITY
        data = {
            benefit_amount:, 
            duration:, 
            monthly: 
        }
    """
    requiredKeys = ['insuranceType']
    res = { 'success': False, 'error': '', 'data': None }

    if (validateRequest(request, requiredKeys, 'GET', res)):
        user = request.user
        insurance_type = request.GET['insuranceType']

        if (insurance_type == 'HEALTH' or insurance_type == 'LIFE' or insurance_type == 'DISABILITY'):
            #depending on the insurance type, the func getQouteHelper is called
            data = getQuoteHelper(user, insurance_type)
            res['data'] = data
            res['success'] = True
        else:
            res['error'] = 'invalid insurance type'
    
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
            data = {
                DISABILITY:{
                    benefit_amount:, 
                    duration:, 
                    monthly: 
                },
                HEALTH: {
                    carrier:,
                    deductible:,
                    deductible_level:,
                    has_spouse:,
                    health_plan_id:,
                    medal:,
                    monthly_premium:,
                    num_kids:,
                    plan_name:,
                    plan_type:,
                },
                LIFE: {
                    age:,
                    carrier:,
                    gender:,
                    life_plan_id:,
                    monthly:
                    policy_amount:
                    policy_term:
                }
            }
    """
    requiredKeys = []
    res = { 'success': False, 'error': '', 'data': None }

    if (validateRequest(request, requiredKeys, 'GET', res)):
        user = request.user

        life_quote = getQuoteHelper(user, 'LIFE')
        health_quote = getQuoteHelper(user, 'HEALTH')
        disability_quote = getQuoteHelper(user, 'DISABILITY')

        data = {'LIFE': life_quote, 'HEALTH': health_quote, 'DISABILITY': disability_quote}

        res['success'] = True
        res['data'] = data
    
    return JsonResponse(res)

@require_GET
def generateInsuranceQuotes(request):
    """
        Generates insurance quotes for a user
        :param request:
        data = {
            GENERAL:{ 
              age: 27, 
              zipcode: '14850', 
              marital_status: 'married', 
              health: 'good', 
              annual_income: '10000', 
              spouse_annual_income: '0', 
              num_kids: '3', 
              kid_ages: [1,2,3],
              gender: 'female' 
            },
            HEALTH: {
              q_1: 'No',
              q_2: 'No', 
              q_5: 'Might go',
              q_6: 'Never or just for my annual physical', 
              q_7: "Drink some tea, it'll pass", 
              q_8: 'Find out cost before booking appt', 
              q_9: 'It crosses my mind sometimes.', 
              q_10: 'It crosses my mind sometimes.',
              q_11: 'Convenient time with any doctor',
              q_12: 'If my doc says so'
            }, 
            LIFE: {
              mortgage_balance: 20000,
              other_debts_balance: 500,
              existing_life_insurance:100,
              balance_investings_savings: 1000,
            }
        }
        :return JsonResponse
        data = {
                DISABILITY:{
                    benefit_amount:, 
                    duration:, 
                    monthly: 
                },
                HEALTH: {
                    carrier:,
                    deductible:,
                    deductible_level:,
                    has_spouse:,
                    health_plan_id:,
                    medal:,
                    monthly_premium:,
                    num_kids:,
                    plan_name:,
                    plan_type:,
                },
                LIFE: {
                    age:,
                    carrier:,
                    gender:,
                    life_plan_id:,
                    monthly:
                    policy_amount:
                    policy_term:
                }
            }

    """
    requiredKeys = ['userData']
    res = { 'success': False, 'error': '', 'data': None }

    if (validateRequest(request, requiredKeys, 'GET', res)):
        #userData fetched from getUserInfo func.
        userData = json.loads(request.GET['userData'])

        general_post = userData['GENERAL']
        life_post = userData['LIFE']
        health_post = userData['HEALTH']

        life_obj = None
        health_obj = None
        general_obj = None
        
        user_kids_ages = []
        is_married = False
        num_kids = 0
        age = 0
        gender = 'male'

        #get general answers
        if (general_post != {}):
            general_post['user_id'] = User()
            
            user_kids_ages = general_post['kid_ages']
            del general_post['kid_ages']

            #get number of kids
            num_kids = asInt(general_post['num_kids'])
            num_kids = min(num_kids, 2)

            #save answers
            general_obj = user_general_answers(**general_post)
        
        #get life answers
        if (life_post != {}):
            life_post['user_id'] = User()
            life_obj = user_life_answers(**life_post)
        
        #get health answers
        if (health_post != {}):
            health_post['user_id'] = User()

            #get every specific answer
            for key in health_post:
                if (key != 'user_id'):
                    if (len(health_post[key]) > 0):
                        #get id
                        num = int(key[key.find('_')+1:])
                        #get specific option_id number
                        # TODO: Make the value of health_post[q_#] be an int [0...2] and index into string array instead of passing
                        # that long string value from the frontend
                        health_post[key] = health_question_options.objects.get(health_question_id = num, option = health_post[key])
                    else:
                        health_post[key] = None
                        
            health_obj = user_health_questions_answer(**health_post)
        
        if (general_obj is not None):
            if (general_obj.marital_status == 'married'):
                is_married= True
            
            #to query db have to map ages to these numbers
            age = str(min([25, 35], key=lambda x:abs(x-int(general_obj.age))))
            gender = general_obj.gender
            
            if gender is 'none' or gender is None:
                gender = 'male'

        health_totals = health_questions.objects.all()

        #run recommendation scripts
        need_insurance, coverage_amount, term = life_insurance(life_obj, general_obj, user_kids_ages)
        plan_type, deductible, critical_illness = health_insurance(health_totals, health_obj)
        benefit_amount_d, duration_d, monthly_d = disability_rec(general_obj)

        health_quote = {}
        life_quote = {}
        disability_quote = {}

        #get health rec
        if (health_plan_costs.objects.filter(plan_type= plan_type, deductible_level = deductible, has_spouse= is_married, num_kids = num_kids).exists()):
            health_quote = health_plan_costs.objects.filter(plan_type= plan_type, deductible_level = deductible, has_spouse= is_married, num_kids = num_kids)[0]
            health_quote = model_to_dict(health_quote)
            health_quote['deductible'] = num_to_usd(health_quote['deductible'])
        
        #get life insurance rec
        if (life_plan_costs.objects.filter(policy_term = term, policy_amount = coverage_amount, gender = gender, age = age).exists()):
            life_quote = life_plan_costs.objects.filter(policy_term = term, policy_amount = coverage_amount, gender = gender, age = age)[0]
            life_quote = model_to_dict(life_quote)
            life_quote['policy_amount'] = abbrev_num_to_usd(life_quote['policy_amount'])
            
        else: #return default value since no match found
            need_insurance, coverage_amount, term = life_insurance(life_insurance_dict = None, general_questions_dict = general_obj, user_kids_age = user_kids_ages) 
            life_quote = life_plan_costs.objects.filter(policy_term = term, policy_amount = coverage_amount, gender = 'female', age = 25)[0] 
            life_quote = model_to_dict(life_quote)

        disability_quote = {'benefit_amount': abbrev_num_to_usd(benefit_amount_d), 'duration': duration_d, 'monthly': num_to_usd(monthly_d)}
             
        data = {'LIFE': life_quote, 'HEALTH': health_quote, 'DISABILITY': disability_quote}

        res['success'] = True
        res['data'] = data

    return JsonResponse(res)

def getQuoteHelper(user, insurance_type):
    """
    Gets insurance quotes for a user based on a type
    :param 
        insurance_type 'HEALTH', 'LIFE' or 'DISABILITY'
        user is User instance 

    :return dictionary data
        data = {
            carrier:,
            deductible:,
            deductible_level:,
            has_spouse:,
            health_plan_id:,
            medal:,
            monthly_premium:,
            num_kids:,
            plan_name:,
            plan_type:,
        }

        if insurance type is LIFE
        data = {
            age:,
            carrier:,
            gender:,
            life_plan_id:,
            monthly:
            policy_amount:
            policy_term:
        }
        
        if insurance type is DISABILITY
        data = {
            benefit_amount:, 
            duration:, 
            monthly: 
        }
    """

    health_info = None
    life_info = None
    gen_answers = None

    is_married = False
    num_kids = 0
    age = 0
    user_kids_age = []

    data = {}
    
    #id the user id is present, then gets all the data form the database
    if (user_general_answers.objects.filter(user_id=user).exists()):
        gen_answers = user_general_answers.objects.get(user_id=user)
        is_married = (gen_answers.marital_status == 'married')
        num_kids = min(gen_answers.num_kids, 2)
        disability_info = user_general_answers.objects.filter(user_id=user.id).values('annual_income')[0]
        age = str(min([25, 35], key=lambda x:abs(x-gen_answers.age)))
        
    if (user_health_questions_answer.objects.filter(user_id=user).exists()):
        health_info = user_health_questions_answer.objects.get(user_id=user)
        
    if (user_life_answers.objects.filter(user_id=user).exists()):
        life_info = user_life_answers.objects.filter(user_id=user.id)[0]    

    if (user_kids.objects.filter(user_id=user).exists()):
        user_kids_age = list(user_kids.objects.values_list('kid_age', flat = True).filter(user_id=user))

    if (insurance_type == 'HEALTH'):
        health_totals = health_questions.objects.all()
        plan_type, deductible, critical_illness = health_insurance(health_totals, health_info)
        num_kids = min(num_kids, 2)

        if (health_plan_costs.objects.filter(plan_type= plan_type, deductible_level = deductible, has_spouse= is_married, num_kids = num_kids).exists()):
            health_quote = health_plan_costs.objects.filter(plan_type= plan_type, deductible_level = deductible, has_spouse= is_married, num_kids = num_kids)[0]
            user_rec = user_recommendation(user_id=user, health_plan_id = health_quote)
            user_rec.save()

            data = model_to_dict(health_quote)
            data['deductible'] = num_to_usd(data['deductible'])
        
    elif (insurance_type == 'LIFE'):
        need_insurance, coverage_amount, term = life_insurance(life_info, gen_answers, user_kids_age)
        gender = 'male' # Default gender if not present
            
        if (gen_answers is not None):
            if gender is not 'none' and gender is not None:
                gender = gen_answers.gender
            
        if (life_plan_costs.objects.filter(policy_term = term, policy_amount = coverage_amount, gender = gender, age = age).exists()):
            life_quote = life_plan_costs.objects.filter(policy_term = term, policy_amount = coverage_amount, gender = gender, age = age)[0]
            user_rec = user_recommendation(user_id=user, life_plan_id = life_quote)
            user_rec.save()
            data = model_to_dict(life_quote)
            data['policy_amount'] = abbrev_num_to_usd(data['policy_amount'])
        else:
            # Return default quote since no match found
            need_insurance, coverage_amount, term = life_insurance(life_insurance_dict = None, general_questions_dict = gen_answers, user_kids_age = user_kids_age) 
            life_quote = life_plan_costs.objects.filter(policy_term = term, policy_amount = coverage_amount, gender = 'female', age = 25)[0]
            user_rec = user_recommendation(user_id=user, life_plan_id = life_quote)
            user_rec.save()
            data = model_to_dict(life_quote)
            data['policy_amount'] = abbrev_num_to_usd(data['policy_amount'])

    elif (insurance_type == 'DISABILITY'):
        benefit_amount_d, duration_d, monthly_d = disability_rec(gen_answers)
        disability_quote = {'benefit_amount': abbrev_num_to_usd(benefit_amount_d), 'duration': duration_d, 'monthly': num_to_usd(monthly_d)}

        # TODO: What to do with disability quotes
        # user_rec = user_recommendation.objects.filter(user_id=user)
        # user_rec.disabililty_plan_id = None
        # user_rec.save()

        data = disability_quote
    
    return data    


def getInsuranceInfoHelper(user, insuranceType):
    """
        Gets insurance info for a user
        :param
            insuranceType = 'HEALTH' | 'LIFE' | 'DISABILITY'
            user = user object

        :return JsonResponse
            { success: bool, error: string, data: object }
            If insuranceType is HEALTH
            data = {
                q_1:, 
                q_2:, 
                q_5:,
                q_6:, 
                q_7:, 
                q_8:, 
                q_9:, 
                q_10:,
                q_11:,
                q_12:
            }
            q_1 is 'Yes' or 'No'
            q_2 is 'Yes' or 'No'
            q_5 is 'No chance', 'Might go', 'I'll definitely go'
            q_6 is '1-3 times besides my physical exam', 'Never or just for my annual physical', or 'More than 3 times a year'
            q_7 is 'More than 3 times a year', 'If I don't feel better in a few days, I'm going to the doctor', or 'Go to the doctor immediately'
            q_8 is 'Do nothing, I feel fine', 'Find out cost before booking appt' or 'Find out cost before booking appt'
            q_9 is 'It crosses my mind sometimes.', 'Not a lot.', or 'Huge worry'
            q_10 is 'It crosses my mind sometimes.', 'Not a lot.', or 'Huge worry'
            q_11 is 'I don't...', 'Convenient time with any doctor', or 'Must see my doc'
            q_12 is 'If my doc says so', 'Not likely', or 'I love second opinions'

            if a user hasnt answered a question, the value will be ''
            if insuranceType is LIFE
            data = {
                mortgage_balance:,
                other_debts_balance:,
                existing_life_insurance:,
                balance_investings_savings:,
            }
    """


    data = {}

    if (insuranceType == 'HEALTH'):
        answers_to_options = user_health_questions_answer.objects.get(user_id=user)
        if (answers_to_options is not None):
            fields = user_health_questions_answer._meta.get_fields()
            for field in fields:
                value = getattr(answers_to_options, field.name)       
                if (value != None and isinstance(value, health_question_options)):
                    data[field.name] = value.option
                elif (value == None):
                    data[field.name] = ""

    elif (insuranceType == 'LIFE'):
        data = list(user_life_answers.objects.filter(user_id=user).values())
        if len(data) > 0:
            data = data[0]
    
    elif (insuranceType == 'DISABILITY'):
        data = list(user_general_answers.objects.filter(user_id=user).values('annual_income'))
        if len(data) > 0:
            data = data[0]

    data.pop('user_id_id', None)
    return data
