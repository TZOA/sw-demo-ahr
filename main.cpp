/********************************************************************************************************************//*
 * @file      %{Cpp:License:FileName}
 * @author    Colin E. Fitzgerald
 * @copyright Copyright © 2019 Clad Innovations Ltd.  All rights reserved.
 **********************************************************************************************************************/
#include <QCoreApplication>
#include <QtCore>
#include <QLoggingCategory>

#include "AhrDemo.h"


int main(int argc, char *argv[]) {
    //QLoggingCategory::setFilterRules(QStringLiteral("qt.bluetooth* = true"));

    QCoreApplication application(argc, argv);

    // Task parented to the application so that it
    // will be deleted by the application.
    AhrDemo *task = new AhrDemo(&application);

    // This will cause the application to exit when
    // the task signals finished.
    QObject::connect(task, SIGNAL(finished()), &application, SLOT(quit()));

    // This will run the task from the application event loop.
    QTimer::singleShot(0, task, SLOT(run()));

    return application.exec();
} // main()

// End of file.
