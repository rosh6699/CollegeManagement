from django.shortcuts import render, get_object_or_404 ,redirect
from django.http import HttpResponseRedirect
from .models import Dept, Class, Student, Attendance, Course, Teacher, Assign, AttendanceTotal, time_slots, DAYS_OF_WEEK, AssignTime, AttendanceClass, StudentCourse, Marks, MarksClass
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
# Create your views here.
from .forms import *
from django.http import HttpResponse
from django.db import connection


@login_required
def index(request):
    if request.user.is_teacher:
        return render(request, 'info/t_homepage.html')
    if request.user.is_student:
        return render(request, 'info/homepage.html')
    return render(request, 'info/logout.html')


@login_required()
def attendance(request, stud_id):
    stud = Student.objects.raw("SELECT * FROM info_student WHERE USN = %s", [stud_id])[0]
    ass_list = Assign.objects.filter(class_id_id=stud.class_id)
    att_list = []
    for ass in ass_list:
        try:
            a = AttendanceTotal.objects.get(student=stud, course=ass.course)
        except AttendanceTotal.DoesNotExist:
            a = AttendanceTotal(student=stud, course=ass.course)
            a.save()
        att_list.append(a)
    return render(request, 'info/attendance.html', {'att_list': att_list})


@login_required()
def attendance_detail(request, stud_id, course_id):
    stud = Student.objects.raw("SELECT * FROM info_student WHERE USN = %s", [stud_id])[0]
    cr = Course.objects.raw("SELECT * FROM info_course WHERE id = %s", [course_id])[0]
    att_list = Attendance.objects.filter(course=cr, student=stud).order_by('date')
    return render(request, 'info/att_detail.html', {'att_list': att_list, 'cr': cr})

@login_required()
def image_upload_view(request,stud_id):
    if request.method == 'POST':
        stud = Student.objects.raw("SELECT * FROM info_student WHERE USN = %s", [stud_id])[0]
        form = ProfileForm(request.POST or None,request.FILES or None, instance=stud)

        if form.is_valid():
            form.save()
            return redirect('success')
    else:
        form = ProfileForm()
    return render(request, 'info/homepage.html', {'form': form})
@login_required()
def success(request):
    return render(request, 'info/homepage.html' )


# def student_search(request, class_id):
#     field = request.POST['fields']
#     search = request.POST['search']
#     class1 = get_object_or_404(Class, id=class_id)
#     if field == 'USN':
#         student_list = class1.student_set.filter(USN__icontains=search)
#     elif field == 'name':
#         student_list = class1.student_set.filter(name__icontains=search)
#     else:
#         student_list = class1.student_set.filter(sex__iexact=search)
#     return render(request, 'info/class1.html', {'class1': class1, 'student_list': student_list})


# Teacher Views

@login_required
def t_clas(request, teacher_id, choice):
    teacher1 = Teacher.objects.raw("SELECT * FROM info_teacher WHERE id = %s", [teacher_id])[0]
    return render(request, 'info/t_clas.html', {'teacher1': teacher1, 'choice': choice})


@login_required()
def t_student(request, assign_id):
    ass = Assign.objects.raw("SELECT * FROM info_assign WHERE id = %s", [assign_id])[0]
    att_list = []
    for stud in ass.class_id.student_set.all():
        try:
            a = AttendanceTotal.objects.get(student=stud, course=ass.course)
        except AttendanceTotal.DoesNotExist:
            a = AttendanceTotal(student=stud, course=ass.course)
            a.save()
        att_list.append(a)
    return render(request, 'info/t_students.html', {'att_list': att_list})

@login_required()
def image_upload_view_t(request,teacher_id):
    if request.method == 'POST':
        teach = Teacher.objects.raw("SELECT * FROM info_teacher WHERE id = %s", [teacher_id])[0]
        form = TeacherProfileForm(request.POST or None,request.FILES or None, instance=teach)

        if form.is_valid():
            form.save()
            return redirect('success_t')
    else:
        form =TeacherProfileForm()
    return render(request, 'info/t_homepage.html', {'form': form})
@login_required()
def success_t(request):
    return render(request, 'info/t_homepage.html' )



@login_required()
def t_class_date(request, assign_id):
    now = timezone.now()
    ass = Assign.objects.raw("SELECT * FROM info_assign WHERE id = %s", [assign_id])[0]
    att_list = ass.attendanceclass_set.filter(date__lte=now).order_by('-date')
    return render(request, 'info/t_class_date.html', {'att_list': att_list})


@login_required()
def cancel_class(request, ass_c_id):
    assc = AttendanceClass.objects.raw("SELECT * FROM info_attendanceclass WHERE id = %s", [ass_c_id])[0]
    #assc.status = 2
    #assc.save()
    sqlexec("UPDATE info_attendanceclass SET status= 2 WHERE id= %s", [ass_c_id])
    return HttpResponseRedirect(reverse('t_class_date', args=(assc.assign_id,)))


@login_required()
def t_attendance(request, ass_c_id):
    assc = AttendanceClass.objects.raw("SELECT * FROM info_attendanceclass WHERE id = %s", [ass_c_id])[0]
    ass = assc.assign
    c = ass.class_id
    context = {
        'ass': ass,
        'c': c,
        'assc': assc,
    }
    return render(request, 'info/t_attendance.html', context)


@login_required()
def edit_att(request, ass_c_id):
    assc = AttendanceClass.objects.raw("SELECT * FROM info_attendanceclass WHERE id = %s", [ass_c_id])[0]
    cr = assc.assign.course
    att_list = Attendance.objects.filter(attendanceclass=assc, course=cr)
    context = {
        'assc': assc,
        'att_list': att_list,
    }
    return render(request, 'info/t_edit_att.html', context)


@login_required()
def confirm(request, ass_c_id):
    assc = AttendanceClass.objects.raw("SELECT * FROM info_attendanceclass WHERE id = %s", [ass_c_id])[0]
    ass = assc.assign
    cr = ass.course
    cl = ass.class_id
    for i, s in enumerate(cl.student_set.all()):
        status = request.POST.get(s.USN)
        if status == 'present':
            status = 1
        else:
            status = 0
        if assc.status == 1:
            try:
                a = Attendance.objects.get(course=cr, student=s, date=assc.date, attendanceclass=assc)
                #a.status = status
                #a.save()
                sqlexec("UPDATE info_attendance SET status= %s WHERE id= %s", [status, a.id])
            except Attendance.DoesNotExist:
                a = Attendance(course=cr, student=s, status=status, date=assc.date, attendanceclass=assc)
                a.save()
        else:
            a = Attendance(course=cr, student=s, status=status, date=assc.date, attendanceclass=assc)
            a.save()
            #assc.status = 1
            #assc.save()
            sqlexec("UPDATE info_attendanceclass SET status= 1 WHERE id= %s", [assc.id])

    return HttpResponseRedirect(reverse('t_class_date', args=(ass.id,)))


@login_required()
def t_attendance_detail(request, stud_id, course_id):
    stud = Student.objects.raw("SELECT * FROM info_student WHERE USN = %s", [stud_id])[0]
    cr = Course.objects.raw("SELECT * FROM info_course WHERE id = %s", [course_id])[0]
    att_list = Attendance.objects.filter(course=cr, student=stud).order_by('date')
    return render(request, 'info/t_att_detail.html', {'att_list': att_list, 'cr': cr})


@login_required()
def change_att(request, att_id):
    a = Attendance.objects.raw("SELECT * FROM info_attendance WHERE id = %s", [att_id])[0]
    #a.status = not a.status
    #a.save()
    sqlexec("UPDATE info_attendance SET status= %s WHERE id= %s", [not a.status, a.id])
    return HttpResponseRedirect(reverse('t_attendance_detail', args=(a.student.USN, a.course_id)))


@login_required()
def t_extra_class(request, assign_id):
    ass = Assign.objects.raw("SELECT * FROM info_assign WHERE id = %s", [assign_id])[0]
    c = ass.class_id
    context = {
        'ass': ass,
        'c': c,
    }
    return render(request, 'info/t_extra_class.html', context)


@login_required()
def e_confirm(request, assign_id):
    ass = Assign.objects.raw("SELECT * FROM info_assign WHERE id = %s", [assign_id])[0]
    cr = ass.course
    cl = ass.class_id
    assc = ass.attendanceclass_set.create(status=1, date=request.POST['date'])
    assc.save()

    for i, s in enumerate(cl.student_set.all()):
        status = request.POST[s.USN]
        if status == 'present':
            status = 'True'
        else:
            status = 'False'
        date = request.POST['date']
        a = Attendance(course=cr, student=s, status=status, date=date, attendanceclass=assc)
        a.save()

    return HttpResponseRedirect(reverse('t_clas', args=(ass.teacher_id,1)))


@login_required()
def t_report(request, assign_id):
    ass = Assign.objects.raw("SELECT * FROM info_assign WHERE id = %s", [assign_id])[0]
    sc_list = []
    for stud in ass.class_id.student_set.all():
        a = StudentCourse.objects.get(student=stud, course=ass.course)
        sc_list.append(a)
    return render(request, 'info/t_report.html', {'sc_list': sc_list})


@login_required()
def timetable(request, class_id):
    
    asst = AssignTime.objects.raw("SELECT * FROM info_assigntime WHERE EXISTS (SELECT * FROM info_assign WHERE info_assign.id = assign_id AND class_id_id = %s)", [class_id])
    
    matrix = [['' for i in range(12)] for j in range(5)]

    for i, d in enumerate(DAYS_OF_WEEK):
        t = 0
        for j in range(12):
            if j == 0:
                matrix[i][0] = d[0]
                continue
            if j == 3 or j == 6:
                continue
            try:
                #a = asst.get(period=time_slots[t][0], day=d[0])
                for a in asst:
                    if a.period == time_slots[t][0] and a.day ==d[0]:
                        class_matrix[i][j] = a.assign.course_id
                        break
                #matrix[i][j] = a.assign.course_id
            except AssignTime.DoesNotExist:
                pass
            t += 1

    context = {'matrix': matrix}
    return render(request, 'info/timetable.html', context)


@login_required()
def t_timetable(request, teacher_id):
    asst = AssignTime.objects.raw("SELECT * FROM info_assigntime WHERE EXISTS (SELECT * FROM info_assign WHERE info_assign.id = assign_id AND teacher_id = %s)", [teacher_id])
    
    class_matrix = [[True for i in range(12)] for j in range(5)]
    for i, d in enumerate(DAYS_OF_WEEK):
        t = 0
        for j in range(12):
            if j == 0:
                class_matrix[i][0] = d[0]
                continue
            if j == 3 or j == 6:
                continue
            try:
                #a = asst.get(period=time_slots[t][0], day=d[0])
                for a in asst:
                    if a.period == time_slots[t][0] and a.day ==d[0]:
                        class_matrix[i][j] = a
                        break
            except AssignTime.DoesNotExist:
                pass
            t += 1

    context = {
        'class_matrix': class_matrix,
    }
    return render(request, 'info/t_timetable.html', context)


@login_required()
def free_teachers(request, asst_id):
    asst = AssignTime.objects.raw("SELECT * FROM info_assigntime WHERE id = %s", [asst_id])[0]
    ft_list = []
    t_list = Teacher.objects.raw("SELECT * FROM info_teacher WHERE EXISTS (SELECT * FROM info_assign WHERE teacher_id = info_teacher.id and class_id_id = %s)", [asst.assign.class_id_id])
    for t in t_list:
        at_list = AssignTime.objects.filter(assign__teacher=t)
        if not any([True if at.period == asst.period and at.day == asst.day else False for at in at_list]):
            ft_list.append(t)

    return render(request, 'info/free_teachers.html', {'ft_list': ft_list})


# student marks


@login_required()
def marks_list(request, stud_id):
    stud = Student.objects.raw("SELECT * FROM info_student WHERE USN = %s", [stud_id])[0]
    ass_list = Assign.objects.filter(class_id_id=stud.class_id)
    sc_list = []
    for ass in ass_list:
        try:
            sc = StudentCourse.objects.get(student=stud, course=ass.course)
        except StudentCourse.DoesNotExist:
            sc = StudentCourse(student=stud, course=ass.course)
            sc.save()
            sc.marks_set.create(type='I', name='Mid Term')
            sc.marks_set.create(type='E', name='Project')
            sc.marks_set.create(type='E', name='Internals')
            sc.marks_set.create(type='S', name='Semester End Exam')
        sc_list.append(sc)

    return render(request, 'info/marks_list.html', {'sc_list': sc_list})


# teacher marks


@login_required()
def t_marks_list(request, assign_id):
    ass = Assign.objects.raw("SELECT * FROM info_assign WHERE id = %s", [assign_id])[0]
    m_list = MarksClass.objects.filter(assign=ass)
    return render(request, 'info/t_marks_list.html', {'m_list': m_list})


@login_required()
def t_marks_entry(request, marks_c_id):
    mc = MarksClass.objects.raw("SELECT * FROM info_marksclass WHERE id = %s", [marks_c_id])[0]
    ass = mc.assign
    c = ass.class_id
    context = {
        'ass': ass,
        'c': c,
        'mc': mc,
    }
    return render(request, 'info/t_marks_entry.html', context)


@login_required()
def marks_confirm(request, marks_c_id):
    mc = MarksClass.objects.raw("SELECT * FROM info_marksclass WHERE id = %s", [marks_c_id])[0]
    ass = mc.assign
    cr = ass.course
    cl = ass.class_id
    for s in cl.student_set.all():
        mark = request.POST[s.USN]
        sc = StudentCourse.objects.get(course=cr, student=s)
        m = sc.marks_set.get(name=mc.name)
        m.marks1 = mark
        m.save()
    mc.status = True
    mc.save()

    return HttpResponseRedirect(reverse('t_marks_list', args=(ass.id,)))


@login_required()
def edit_marks(request, marks_c_id):
    mc = MarksClass.objects.raw("SELECT * FROM info_marksclass WHERE id = %s", [marks_c_id])[0]
    cr = mc.assign.course
    stud_list = mc.assign.class_id.student_set.all()
    m_list = []
    for stud in stud_list:
        sc = StudentCourse.objects.get(course=cr, student=stud)
        m = sc.marks_set.get(name=mc.name)
        m_list.append(m)
    context = {
        'mc': mc,
        'm_list': m_list,
    }
    return render(request, 'info/edit_marks.html', context)


@login_required()
def student_marks(request, assign_id):
    ass = Assign.objects.raw("SELECT * FROM info_assign WHERE id = %s", [assign_id])[0]
    sc_list = StudentCourse.objects.filter(student__in=ass.class_id.student_set.all(), course=ass.course)
    return render(request, 'info/t_student_marks.html', {'sc_list': sc_list})



def sqlexec(squery, var=[]):
    cursor= connection.cursor()
    if len(var)==0:
        cursor.execute(squery)
    else:
        cursor.execute(squery, var)




