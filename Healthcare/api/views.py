from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Health
from .serializers import Healthserializer
from rest_framework.permissions import IsAuthenticated
from .permission import IsOwnerOrReadOnly
from django.db.models import Q
from drf_yasg import openapi


# we use this when we use JWTAuthentication
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema

class HealthcenterView(APIView):

    # for Session or JWT this code remains a same for both Authenticatoin
    permission_classes = [IsAuthenticated,IsOwnerOrReadOnly]

    @swagger_auto_schema(
    operation_description="Get user health records",
        manual_parameters=[
            openapi.Parameter('Email', openapi.IN_QUERY, description="Filter by email", type=openapi.TYPE_STRING),
            openapi.Parameter('search', openapi.IN_QUERY, description="Search name/email", type=openapi.TYPE_STRING),
            openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter('limit', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
        ]
    )

    def get(self,request,Email=None):

        # Filtering and search starts from here

        # Get only records that belong to currently logged-in user(by user_id)
        queryset = Health.objects.filter(user=request.user)

        # this gets query parameter from URL and in query it Get query parameter from URL
        #  (e.g., ?Email=test@gmail.com)

        email = request.query_params.get('Email')

        # Check if Email parameter is provided in URL
        if email:

            # It filter email which you get from URL with Email field from Health model
            queryset = queryset.filter(Email=email)
        
        search = request.query_params.get('search')
        if search:

            # Split search string into multiple words(ex. darshit darshit@gmail.com , [darshit,darshit@...])

            terms = search.split()

            # Q object helps build complex queries (OR, AND conditions)
            query = Q()

            for term in terms:

                # Here make a query and pass in to query variable
                query |= Q(name__icontains=term)
                query |= Q(Email__icontains=term)
            queryset = queryset.filter(query)


        # Pagination starts from here

        # This is get a query like page and limit and store(type is string) it into a variables named below. 
        page = request.query_params.get('page',1)
        limit = request.query_params.get('limit',5)

        # here you convert into int for doing calculation

        page = int(page)
        limit = int(limit)

        # Math calculation for set pages and how many record you want to show in one page(by setting up a limit)
        start = (page - 1)*limit
        end = start + limit

        # this for count for how many records are there in a page
        total_records = queryset.count()

        # this is for slicing
        queryset = queryset[start:end]

        # Convert queryset (model objects) into JSON-serializable data
        serializer = Healthserializer(queryset,many=True)

        # Return response and convert Python data into JSON format
        return Response({
            "Total_records": total_records,
            "page": page,
            "limit": limit,
            "data": serializer.data
        })

    @swagger_auto_schema(
        operation_description="Create new health record",
        request_body=Healthserializer,
        responses={201: Healthserializer}
    )
    def post(self,request,Email=None):

        # Here you do deserialization and send data by context to validation method which is in serializer
        serializer = Healthserializer(data = request.data,context={'request':request})

        # this validate user and grant permission to user to do post opration on only their data
        if serializer.is_valid():

            # Save data and assign current user as owner
            serializer.save(user=request.user)

            # Here you return data and ,
            # status(this status for JWTAuthentication if you not usig it then this is optional)
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Delete health record by Email",
        request_body=None  # 🔥 THIS IS THE FIX
    )
    def delete(self,request,Email=None):
        try:

            # Here you get your data by matching a Email and user_id(this for give only perticuler user's data)
            h = Health.objects.get(Email=Email,user = request.user)
           
        except Health.DoesNotExist:
            return Response({'error': 'Health record not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user has permission to delete this object
        self.check_object_permissions(request, h)

        # Deleting data
        h.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @swagger_auto_schema(
        request_body=Healthserializer,
        operation_description="Create new health record",
        responses={200: Healthserializer}
    )
    def put(self,request,Email=None):

        try:
            h = Health.objects.get(Email=Email,user = request.user)
            self.check_object_permissions(request, h)  
            serializer = Healthserializer(h,data = request.data,context = {'request':request})
            
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Health.DoesNotExist:
            return Response({'error': 'Health record not found'}, status=status.HTTP_404_NOT_FOUND)

def home(request):
    return HttpResponse("Welcome to HealthcareCenter")